import argparse
import csv
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE / ".env")

MODEL = os.getenv("LLM_MODEL", "groq/openai/gpt-oss-20b")
DATA = HERE / "data" / "pharmacy_stock.csv"
EVIDENCE = HERE / "evidence"


def require_key():
    prefix = MODEL.split("/", 1)[0]
    needed = {
        "groq": "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }.get(prefix)
    if needed and not os.getenv(needed):
        raise SystemExit(f"{needed} is not set. Add it to {HERE.parent / '.env'}.")


def compact(value):
    return "".join(str(value).lower().split())


def check_stock(item: str, strength: str = "") -> list[dict]:
    with DATA.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    needle = compact(item)
    strength_key = compact(strength)
    hits = []
    for row in rows:
        if needle in compact(row["item"]) and (
            not strength_key or strength_key == compact(row["strength"])
        ):
            hits.append(
                {
                    "item": row["item"],
                    "strength": row["strength"],
                    "form": row["form"],
                    "quantity": int(row["quantity"]),
                    "unit_price_ghs": float(row["unit_price_ghs"]),
                    "expiry_date": row["expiry_date"],
                    "days_left": (date.fromisoformat(row["expiry_date"]) - date.today()).days,
                }
            )
    return hits


TOOLS = {"check_stock": check_stock}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": (
                "Look up a medicine in the pharmacy stock list. Returns rows with item, "
                "strength, form, quantity, unit_price_ghs, expiry_date and days_left. "
                "Use it before answering any question about availability, price or expiry."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "Medicine name, for example amoxicillin",
                    },
                    "strength": {
                        "type": "string",
                        "description": "Strength such as 500mg. Omit to return all strengths.",
                    },
                },
                "required": ["item"],
            },
        },
    }
]

SYSTEM_PROMPT = (
    "You are the stock assistant of a community pharmacy in Accra, Ghana. "
    "Always call check_stock before answering a stock, price or expiry question. "
    "Never invent a quantity, price or date. If the tool returns no rows, say the "
    "item is not stocked."
)


def ask(question):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    response = completion(
        model=MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
        temperature=0,
    )
    message = response.choices[0].message
    print("\nassistant message 1")
    print(f"content: {message.content!r}")

    calls = getattr(message, "tool_calls", None)
    if not calls:
        print("No tool call; answer taken as-is.")
        return message.content or ""

    messages.append(
        {
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": call.id or f"call_{index}",
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                for index, call in enumerate(calls, 1)
            ],
        }
    )

    for index, call in enumerate(calls, 1):
        name = call.function.name
        arguments = json.loads(call.function.arguments or "{}")
        print(f"tool_call: {name}({arguments})")
        result = TOOLS[name](**arguments)
        print(f"tool result: {json.dumps(result)[:400]}")
        messages.append(
            {
                "role": "tool",
                "tool_call_id": call.id or f"call_{index}",
                "content": json.dumps(result),
            }
        )

    response = completion(
        model=MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
        temperature=0,
    )
    answer = response.choices[0].message.content or ""
    print("\nassistant message 2")
    print(answer)
    return answer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", action="append", default=[])
    args = parser.parse_args()
    questions = args.question or [
        "Do we have amoxicillin 500mg?",
        "What do 2 packs of paracetamol 500mg cost?",
        "How many amoxicillin 250mg packs are left and when do they expire?",
    ]

    require_key()
    EVIDENCE.mkdir(exist_ok=True)
    lines = [
        f"# native function calling on {MODEL}",
        f"# tools: {list(TOOLS)}",
        "",
    ]

    for index, question in enumerate(questions, 1):
        if index > 1:
            time.sleep(8)
        lines.append("=" * 72)
        lines.append(f"QUESTION: {question}")
        try:
            final = ask(question)
            lines.append(f"\nFINAL ANSWER: {final}")
        except Exception as exc:
            lines.append(f"\nERROR: {type(exc).__name__}: {exc}")
        lines.append("")

    out = EVIDENCE / "function_calling.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nEvidence written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
