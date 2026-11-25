import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from agent.faq_agent import run

CASES = HERE / "cases.jsonl"
RESULTS = HERE.parent / "evidence" / "eval_results.md"


import unicodedata

def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    return " ".join(text.split())

def grade(case, result):
    answer = normalize(result["answer"]).lower()
    tool_names = [c["name"] for c in result["tool_calls"]]
    must_ok = all(normalize(term).lower() in answer for term in case.get("must_include", []))
    expected = case.get("expected_tools")
    if expected is None:
        tools_ok = True
    else:
        tools_ok = set(expected).issubset(set(tool_names)) if expected else (len(tool_names) == 0)
    return must_ok and tools_ok, must_ok, tools_ok


def main():
    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]
    RESULTS.parent.mkdir(exist_ok=True)
    rows = []
    total_tokens = 0
    total_latency = 0.0
    passed = 0

    for case in cases:
        result = run(case["input"])
        ok, must_ok, tools_ok = grade(case, result)
        passed += int(ok)
        total_tokens += result["tokens"].get("prompt", 0) + result["tokens"].get("completion", 0)
        total_latency += result["latency_s"]
        rows.append((case, result, ok, must_ok, tools_ok))
        print(f"{case['id']}: {'PASS' if ok else 'FAIL'}  tools={result['tool_calls']}")

    lines = ["# Lab 10 Eval Results", "", f"Cases: {len(cases)}", f"Passed: {passed}", ""]
    lines.append("| ID | Category | Pass | Must-include | Tools | Latency (s) | Tokens |")
    lines.append("|---|---|---|---|---|---|---|")
    for case, result, ok, must_ok, tools_ok in rows:
        tools = ",".join(c["name"] for c in result["tool_calls"]) or "-"
        toks = result["tokens"].get("prompt", 0) + result["tokens"].get("completion", 0)
        lines.append(
            f"| {case['id']} | {case['category']} | {'PASS' if ok else 'FAIL'} | "
            f"{'ok' if must_ok else 'MISSING'} | {tools} | {result['latency_s']} | {toks} |"
        )
    lines.append("")
    lines.append(f"Total tokens: {total_tokens}")
    lines.append(f"Average latency: {round(total_latency / len(cases), 3)}s")
    lines.append(f"Cost estimate: tokens only (no price applied).")
    RESULTS.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nResults written to {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
