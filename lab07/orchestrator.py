import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
EVIDENCE = HERE / "evidence"
VENUES = json.loads((DATA / "venues.json").read_text(encoding="utf-8"))["venues"]
CATERERS = json.loads((DATA / "caterers.json").read_text(encoding="utf-8"))["caterers"]

DEFAULT_GUESTS = 80
DEFAULT_BUDGET = 20000
CONVERSATION = "event-001"


def message(sender, receiver, performative, content):
    return {
        "conversation_id": CONVERSATION,
        "sender": sender,
        "receiver": receiver,
        "performative": performative,
        "content": content,
    }


def venue_agent(request):
    guests = request["guests"]
    budget = request["budget"]
    remaining_for_catering = budget  # venue will leave room
    candidates = []
    for venue in VENUES:
        if venue["capacity"] >= guests and venue["cost_ghs"] <= budget - 1500:
            candidates.append(venue)
    if not candidates:
        return None, "refuse"
    # pick cheapest feasible venue
    chosen = min(candidates, key=lambda v: v["cost_ghs"])
    return chosen, "propose"


def catering_agent(request):
    guests = request["guests"]
    remaining = request["remaining_budget"]
    venue = request["venue"]
    needs_ok = set(venue.get("constraints", []))
    candidates = []
    for caterer in CATERERS:
        if caterer["min_guests"] > guests:
            continue
        cost = caterer["price_per_head_ghs"] * guests
        if cost > remaining:
            continue
        # check needs
        venue_has_kitchen = venue.get("has_kitchen", False)
        venue_outdoor = "outdoor" in " ".join(venue.get("constraints", [])).lower()
        needs = caterer.get("needs", [])
        ok = True
        for need in needs:
            if "kitchen access" in need and not venue_has_kitchen:
                ok = False
            if "open-flame" in need and "no open flames indoors" in " ".join(venue.get("constraints", [])):
                if not venue_outdoor:
                    ok = False
            if "outdoor space" in need and not venue_outdoor:
                ok = False
        if ok:
            candidates.append((caterer, cost))
    if not candidates:
        return None, "refuse"
    chosen, cost = min(candidates, key=lambda pair: pair[1])
    return {"caterer": chosen, "cost": cost}, "propose"


def run(guests=DEFAULT_GUESTS, budget=DEFAULT_BUDGET):
    EVIDENCE.mkdir(exist_ok=True)
    log = []

    def emit(msg):
        log.append(msg)
        print(f"{msg['sender']} -> {msg['receiver']}: {msg['performative']} | {msg['content']}")

    emit(message("User", "EventPlanner", "request",
                 f"Plan an event for {guests} guests with a total budget of GHS {budget}."))

    emit(message("EventPlanner", "VenueAgent", "request",
                 f"Find a venue for {guests} guests, budget up to GHS {budget - 1500}."))

    venue, perf = venue_agent({"guests": guests, "budget": budget})
    if venue is None:
        emit(message("VenueAgent", "EventPlanner", "refuse",
                     "No venue fits the budget and capacity constraints."))
        emit(message("EventPlanner", "User", "inform",
                     "Sorry, no venue is available for your budget."))
        write_log(log)
        return

    emit(message("VenueAgent", "EventPlanner", "propose",
                 f"{venue['name']} ({venue['location']}), capacity {venue['capacity']}, "
                 f"cost GHS {venue['cost_ghs']}. Constraints: {', '.join(venue['constraints'])}."))

    remaining = budget - venue["cost_ghs"]
    emit(message("EventPlanner", "CateringAgent", "request",
                 f"Cater for {guests} guests with GHS {remaining} remaining, "
                 f"venue needs: kitchen={venue['has_kitchen']}, "
                 f"constraints={venue['constraints']}."))

    result, perf = catering_agent({"guests": guests, "remaining_budget": remaining, "venue": venue})
    if result is None:
        emit(message("CateringAgent", "EventPlanner", "refuse",
                     "No caterer fits the remaining budget and venue constraints."))
        emit(message("EventPlanner", "User", "inform",
                     f"Venue {venue['name']} found, but no caterer fits the budget."))
        write_log(log)
        return

    caterer = result["caterer"]
    cost = result["cost"]
    emit(message("CateringAgent", "EventPlanner", "propose",
                 f"{caterer['name']}, {caterer['price_per_head_ghs']} GHS/head, "
                 f"total GHS {cost}. Package: {caterer['packages']['standard']}."))

    total = venue["cost_ghs"] + cost
    emit(message("EventPlanner", "User", "inform",
                 f"Plan ready: {venue['name']} (GHS {venue['cost_ghs']}) + "
                 f"{caterer['name']} (GHS {cost}) = GHS {total} of GHS {budget}."))

    write_log(log)


def write_log(log):
    EVIDENCE.mkdir(exist_ok=True)
    with (EVIDENCE / "messages.jsonl").open("w", encoding="utf-8") as handle:
        for msg in log:
            handle.write(json.dumps(msg, ensure_ascii=False) + "\n")
    print(f"\nLog written to {EVIDENCE / 'messages.jsonl'} ({len(log)} messages)")


AGENT_CARDS = [
    {
        "name": "EventPlanner",
        "description": "Orchestrates event planning: delegates to VenueAgent and CateringAgent.",
        "url": "http://localhost:8000/planner",
        "skills": [{"name": "plan_event", "description": "Plan an event given guest count and budget."}],
    },
    {
        "name": "VenueAgent",
        "description": "Finds a suitable venue for a given guest count and budget.",
        "url": "http://localhost:8001/venue",
        "skills": [{"name": "find_venue", "description": "Return a venue proposal or refuse."}],
    },
    {
        "name": "CateringAgent",
        "description": "Finds a suitable caterer within a remaining budget and venue constraints.",
        "url": "http://localhost:8002/catering",
        "skills": [{"name": "find_caterer", "description": "Return a caterer proposal or refuse."}],
    },
]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--guests", type=int, default=DEFAULT_GUESTS)
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    args = parser.parse_args()

    # write agent cards
    (HERE / "agent_cards.json").write_text(
        json.dumps(AGENT_CARDS, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Agent cards written.")
    run(args.guests, args.budget)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
