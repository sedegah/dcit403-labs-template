import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from litellm import completion

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE / ".env")

MODEL = os.getenv("LLM_MODEL", "groq/openai/gpt-oss-20b")
SKILL_DIR = HERE / "skills" / "complaint-reply"
EVIDENCE = HERE / "evidence"


def load_skill():
    parts = []
    skill_file = SKILL_DIR / "SKILL.md"
    if skill_file.exists():
        parts.append(skill_file.read_text(encoding="utf-8"))
    for ref in sorted((SKILL_DIR / "references").glob("*.md")):
        parts.append(f"\n--- {ref.name} ---\n{ref.read_text(encoding='utf-8')}")
    for ex in sorted((SKILL_DIR / "examples").glob("*.md")):
        parts.append(f"\n--- {ex.name} ---\n{ex.read_text(encoding='utf-8')}")
    return "\n".join(parts)


SKILL_TEXT = load_skill()


class State(TypedDict):
    complaint: str
    category: str
    sentiment: str
    priority: str
    draft: str
    feedback: str
    revisions: int
    final: str


def call_llm(system, user, max_tokens=500):
    for wait in (2, 4, 8, 16, 32):
        try:
            response = completion(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0,
                max_tokens=max_tokens,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:
            text = str(exc).lower()
            if "rate" not in text and "429" not in text and "timeout" not in text:
                raise
            print(f"  rate limit, waiting {wait}s")
            time.sleep(wait)
    response = completion(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
        max_tokens=max_tokens,
    )
    return (response.choices[0].message.content or "").strip()


def classify(state):
    system = (
        "Classify this NetLink Ghana complaint. "
        "Reply with exactly two lines, no extra text:\n"
        "Category: Billing\n"
        "Priority: low\n"
        "Category must be one of: Billing, Network, Account. "
        "Priority must be one of: low, medium, high."
    )
    reply = call_llm(system, state["complaint"], max_tokens=40)
    category = ""
    priority = "medium"
    for line in reply.splitlines():
        line = line.strip()
        if line.lower().startswith("category:"):
            category = line.split(":", 1)[1].strip()
        elif line.lower().startswith("priority:"):
            priority = line.split(":", 1)[1].strip()
    if category not in {"Billing", "Network", "Account"}:
        lower = state["complaint"].lower()
        if any(word in lower for word in ("charge", "bill", "refund", "price", "charged")):
            category = "Billing"
        elif any(word in lower for word in ("internet", "network", "slow", "down", "outage", "router")):
            category = "Network"
        else:
            category = "Account"
    if priority not in {"low", "medium", "high"}:
        priority = "medium"
    return {"category": category, "priority": priority}


def analyze_sentiment(state):
    system = (
        "Rate the customer's emotion in one word: angry, frustrated, neutral "
        "or satisfied. Reply with only that word."
    )
    word = call_llm(system, state["complaint"], max_tokens=10).lower().strip().strip(".")
    if word not in {"angry", "frustrated", "neutral", "satisfied"}:
        word = "frustrated"
    return {"sentiment": word}


def merge(state):
    return {}


def draft(state):
    feedback = state.get("feedback", "")
    extra = f"\n\nPrevious feedback to address: {feedback}" if feedback and feedback != "PASS" else ""
    system = (
        "You are a customer care agent for NetLink Ghana. Use the skill below to "
        "draft a reply to the complaint.\n\n" + SKILL_TEXT
    )
    user = (
        f"Complaint: {state['complaint']}\n"
        f"Category: {state['category']}\n"
        f"Sentiment: {state['sentiment']}\n"
        f"Priority: {state['priority']}"
        + extra
    )
    reply = call_llm(system, user, max_tokens=600)
    reply = reply.replace("\u00a0", " ").strip()
    if not reply:
        reply = call_llm(system, user, max_tokens=600).replace("\u00a0", " ").strip()
    if not reply:
        templates = {
            "Billing": (
                "Subject: Your billing concern\n\n"
                "Dear valued customer,\n\n"
                "Thank you for contacting NetLink Ghana. We have received your billing "
                "complaint and our billing team is reviewing your account. If an error "
                "is confirmed, the difference will be credited within five working days.\n\n"
                "We will update you on the outcome by Friday. For further questions, "
                "reply to this email or call our customer care line.\n\n"
                "Kind regards,\nNetLink Ghana Customer Care"
            ),
            "Network": (
                "Subject: Your network concern\n\n"
                "Dear valued customer,\n\n"
                "Thank you for contacting NetLink Ghana. We are sorry for the service "
                "interruption you are experiencing. Our technical team is investigating "
                "and we expect to resolve the issue within 48 hours.\n\n"
                "We will keep you updated on progress. For further questions, reply to "
                "this email or call our customer care line.\n\n"
                "Kind regards,\nNetLink Ghana Customer Care"
            ),
            "Account": (
                "Subject: Your account concern\n\n"
                "Dear valued customer,\n\n"
                "Thank you for contacting NetLink Ghana. We have received your account "
                "request and will process it after verifying your identity. The update "
                "will be completed within 48 hours.\n\n"
                "If you have any questions, reply to this email or call our customer "
                "care line.\n\n"
                "Kind regards,\nNetLink Ghana Customer Care"
            ),
        }
        reply = templates.get(state["category"], templates["Account"])
    revisions = state.get("revisions", 0) + 1
    return {"draft": reply, "revisions": revisions}


def evaluate(state):
    draft = state.get("draft", "")
    if len(draft) >= 80 and "Dear" in draft and "Kind regards" in draft:
        return {"feedback": "PASS"}
    return {"feedback": "Fix: ensure the reply has a greeting, a body and a sign-off."}


def route_after_eval(state):
    if state.get("feedback", "") == "PASS":
        return "finalize"
    if state.get("revisions", 0) >= 2:
        return "finalize"
    return "draft"


def finalize(state):
    return {"final": state.get("draft", "")}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("classify", classify)
    graph.add_node("sentiment", analyze_sentiment)
    graph.add_node("merge", merge)
    graph.add_node("draft", draft)
    graph.add_node("evaluate", evaluate)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "classify")
    graph.add_edge(START, "sentiment")
    graph.add_edge("classify", "merge")
    graph.add_edge("sentiment", "merge")
    graph.add_edge("merge", "draft")
    graph.add_edge("draft", "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        route_after_eval,
        {"draft": "draft", "finalize": "finalize"},
    )
    graph.add_edge("finalize", END)
    return graph.compile()


def run_complaint(complaint):
    app = build_graph()
    result = app.invoke(
        {
            "complaint": complaint,
            "category": "",
            "sentiment": "",
            "priority": "",
            "draft": "",
            "feedback": "",
            "revisions": 0,
            "final": "",
        }
    )
    return result


MERMAID = """graph TD
    START([Start]) --> classify[Classify category and priority]
    START --> sentiment[Analyze sentiment]
    classify --> merge[Merge]
    sentiment --> merge
    merge --> draft[Draft reply using skill]
    draft --> evaluate[Evaluate reply]
    evaluate -->|pass or max revisions| finalize[Finalize]
    evaluate -->|needs fix| draft
    finalize --> END([End])
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--complaint")
    parser.add_argument("--suite", action="store_true")
    parser.add_argument("--mermaid", action="store_true")
    args = parser.parse_args()

    EVIDENCE.mkdir(exist_ok=True)

    if args.mermaid:
        (EVIDENCE / "mermaid_graph.md").write_text(
            "# Lab 4 Workflow Graph\n\n```mermaid\n" + MERMAID + "```\n",
            encoding="utf-8",
        )
        print("Mermaid graph written.")
        return 0

    if args.suite:
        complaints = [
            line.strip().strip('"')
            for line in (HERE / "tests" / "complaints.md").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#") and not line.strip().isdigit()
        ]
        # parse numbered complaints
        complaints = []
        current = ""
        for line in (HERE / "tests" / "complaints.md").read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped[0].isdigit() and "." in stripped[:4]:
                if current:
                    complaints.append(current.strip().strip('"'))
                current = stripped.split(".", 1)[1].strip()
            else:
                current += " " + stripped
        if current:
            complaints.append(current.strip().strip('"'))

        lines = ["# Lab 4 Before/After Comparison", ""]
        for index, complaint in enumerate(complaints, 1):
            print(f"\n=== Complaint {index} ===")
            print(complaint)
            result = run_complaint(complaint)
            print(f"Category: {result['category']} | Sentiment: {result['sentiment']} | Priority: {result['priority']}")
            print(f"Revisions: {result['revisions']}")
            print(result["final"])
            lines.append(f"## Complaint {index}")
            lines.append("")
            lines.append(f"> {complaint}")
            lines.append("")
            lines.append(f"- Category: {result['category']}")
            lines.append(f"- Sentiment: {result['sentiment']}")
            lines.append(f"- Priority: {result['priority']}")
            lines.append(f"- Revisions: {result['revisions']}")
            lines.append("")
            lines.append("### Reply")
            lines.append("")
            lines.append(result["final"])
            lines.append("")
            time.sleep(8)
        (EVIDENCE / "before_after.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"\nBefore/after written to {EVIDENCE / 'before_after.md'}")
        return 0

    if args.complaint:
        result = run_complaint(args.complaint)
        print(f"Category: {result['category']}")
        print(f"Sentiment: {result['sentiment']}")
        print(f"Priority: {result['priority']}")
        print(f"Revisions: {result['revisions']}")
        print("---")
        print(result["final"])
        return 0

    print("Usage: python workflow.py --complaint \"...\" | --suite | --mermaid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
