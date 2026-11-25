import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE / ".env")

MODEL = os.getenv("LAB2_MODEL", "groq/qwen/qwen3.8-27b")
EVIDENCE = HERE / "evidence"
RETRY_WAITS = (2, 4, 8, 16)

BUDGET = (
    "I have GHS 1,200. I want 4 bags of rice at GHS 185 each and 3 gallons "
    "of oil at GHS 95 each. How much will I have left?"
)

FACTUAL = [
    "What is the capital of the Bono East Region of Ghana?",
    "Who founded Makola Market in Accra?",
]


def call_model(question):
    for wait in (*RETRY_WAITS, None):
        try:
            response = completion(
                model=MODEL,
                messages=[{"role": "user", "content": question}],
                temperature=0,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:
            text = f"{type(exc).__name__}: {exc}".lower()
            retryable = any(
                marker in text
                for marker in (
                    "rate limit",
                    "ratelimit",
                    "429",
                    "connection",
                    "timeout",
                    "overloaded",
                    "503",
                )
            )
            if not retryable or wait is None:
                raise
            print(f"  model error, retrying in {wait}s")
            time.sleep(wait)


def cell(text):
    return " ".join(text.split()).replace("|", "\\|")


def main():
    EVIDENCE.mkdir(exist_ok=True)
    budget_runs = []
    factual_runs = []

    for index in range(1, 4):
        print(f"budget run {index}")
        answer = call_model(BUDGET)
        budget_runs.append(answer)
        if index < 3:
            time.sleep(3)

    for question in FACTUAL:
        print(f"factual: {question}")
        factual_runs.append((question, call_model(question)))
        time.sleep(3)

    lines = [
        "# Lab 2 Baseline: Model With No Tools",
        "",
        f"Model: `{MODEL}`",
        f"Run: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Budget question",
        "",
        f"> {BUDGET}",
        "",
        "Correct answer: **GHS 175** (1,200 - 740 - 285).",
        "",
        "| Run | Model answer | Correct? |",
        "|---|---|---|",
    ]

    for index, answer in enumerate(budget_runs, 1):
        correct = "Yes" if "175" in answer else "No"
        lines.append(f"| {index} | {cell(answer)} | {correct} |")

    lines += [
        "",
        "## Factual questions",
        "",
        "| Question | Model answer |",
        "|---|---|",
    ]

    for question, answer in factual_runs:
        lines.append(f"| {cell(question)} | {cell(answer)} |")

    lines += [
        "",
        "## Observation",
        "",
        "_Written after reading the runs above._",
        "",
    ]

    out = EVIDENCE / "baseline.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nBaseline written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
