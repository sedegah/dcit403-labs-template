import argparse
import csv
import os
import sys
from datetime import date, datetime
from pathlib import Path

from langgraph.graph import END, START, StateGraph
from typing import TypedDict

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "orders.csv"
EVIDENCE = HERE / "evidence"
REFUND_CSV = HERE / "manual_refunds.csv"
REFUND_WINDOW_DAYS = 14


class State(TypedDict):
    order_id: str
    customer: str
    item: str
    total: float
    order_date: str
    eligible: bool
    reason: str
    approved: bool
    outcome: str
    refund_id: str


def load_order(state):
    with open(DATA, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["order_id"] == state["order_id"]:
                total = float(row["item_price_ghs"]) + float(row["delivery_ghs"])
                return {
                    "customer": row["customer"],
                    "item": row["item"],
                    "total": total,
                    "order_date": row["order_date"],
                    "refunded": row["refunded"],
                }
    raise ValueError(f"Order {state['order_id']} not found")


def check_eligibility(state):
    if state.get("refunded") == "yes":
        return {"eligible": False, "reason": "already refunded"}
    try:
        order_date = date.fromisoformat(state["order_date"])
    except ValueError:
        return {"eligible": False, "reason": "bad date"}
    age = (date.today() - order_date).days
    if age > REFUND_WINDOW_DAYS:
        return {"eligible": False, "reason": f"outside 14-day window ({age} days)"}
    if state["total"] <= 0:
        return {"eligible": False, "reason": "non-positive amount"}
    return {"eligible": True, "reason": f"within window ({age} days)"}


def route_after_check(state):
    return "request_approval" if state["eligible"] else "reject"


def request_approval(state):
    # In non-interactive mode the decision is supplied via state["approved"].
    approved = state.get("approved", False)
    return {"approved": approved}


def route_after_approval(state):
    return "process_refund" if state["approved"] else "reject"


def process_refund(state):
    refund_id = f"RF-{state['order_id']}"
    EVIDENCE.mkdir(exist_ok=True)
    exists = REFUND_CSV.exists()
    with open(REFUND_CSV, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if not exists:
            writer.writerow(["refund_id", "order_id", "customer", "amount_ghs", "date"])
        writer.writerow([refund_id, state["order_id"], state["customer"],
                        f"{state['total']:.2f}", date.today().isoformat()])
    return {"outcome": "refunded", "refund_id": refund_id}


def reject(state):
    reason = state.get("reason", "not approved")
    if state.get("eligible") and not state.get("approved", False):
        reason = "approver rejected"
    return {"outcome": f"rejected: {reason}"}


def finalize(state):
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("load_order", load_order)
    g.add_node("check_eligibility", check_eligibility)
    g.add_node("request_approval", request_approval)
    g.add_node("process_refund", process_refund)
    g.add_node("reject", reject)
    g.add_node("finalize", finalize)

    g.add_edge(START, "load_order")
    g.add_edge("load_order", "check_eligibility")
    g.add_conditional_edges("check_eligibility", route_after_check,
                            {"request_approval": "request_approval", "reject": "reject"})
    g.add_conditional_edges("request_approval", route_after_approval,
                            {"process_refund": "process_refund", "reject": "reject"})
    g.add_edge("process_refund", "finalize")
    g.add_edge("reject", "finalize")
    g.add_edge("finalize", END)
    return g.compile()


def run(order_id, approved=False):
    app = build_graph()
    result = app.invoke({
        "order_id": order_id,
        "customer": "",
        "item": "",
        "total": 0.0,
        "order_date": "",
        "eligible": False,
        "reason": "",
        "approved": approved,
        "outcome": "",
        "refund_id": "",
    })
    trace = [
        f"Order: {result['order_id']} ({result['customer']})",
        f"Item: {result['item']}",
        f"Total: GHS {result['total']:.2f}",
        f"Order date: {result['order_date']}",
        f"Eligible: {result['eligible']} ({result['reason']})",
        f"Approved: {result['approved']}",
        f"Outcome: {result['outcome']}",
    ]
    if result.get("refund_id"):
        trace.append(f"Refund ID: {result['refund_id']}")
    text = "\n".join(trace)
    print(text)
    print("=" * 50)
    EVIDENCE.mkdir(exist_ok=True)
    tag = f"trace_{order_id}.txt"
    (EVIDENCE / tag).write_text(text + "\n", encoding="utf-8")
    return result


CASES = [
    ("KM1008", True),   # eligible, approved
    ("KM1005", True),   # eligible, approved
    ("KM1001", False),  # eligible, rejected
    ("KM1004", True),   # outside window
    ("KM1006", True),   # already refunded
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--order")
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--suite", action="store_true")
    args = parser.parse_args()

    if args.suite:
        for order_id, approved in CASES:
            run(order_id, approved=approved)
        return 0
    if args.order:
        run(args.order, approved=args.approve)
        return 0
    print("Usage: python refund_graph.py --order ID [--approve] | --suite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
