import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion
from litellm.exceptions import BadRequestError

from tools import TOOL_DESCRIPTIONS, TOOL_NAMES, TOOLS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE / ".env")

MODEL = os.getenv("LAB2_MODEL", "groq/qwen/qwen3.8-27b")
EVIDENCE = HERE / "evidence"
MAX_STEPS = 8
RETRY_WAITS = (2, 4, 8, 16)

SYSTEM_PROMPT = f"""You are a careful assistant for a trader at Makola Market in Accra, Ghana.

You do not have function calling. Never emit JSON tool calls and never use a
tools field. Choose every action as plain text and the program will run it.

Available actions:
{TOOL_DESCRIPTIONS}
- finish: gives the final answer to the user

Reply with exactly these three lines and nothing else:

Thought: <one or two sentences of reasoning>
Action: {TOOL_NAMES}
Action Input: <input for the action, or the complete final answer if finish>

Rules:
1. Never do arithmetic in your head. Call calculator for every sum, product,
   subtraction and division, including the final subtraction.
2. Use wiki_lookup for facts about places, people and history.
3. Never write an Observation line. The program runs the action and sends the
   Observation back to you.
4. If an action returns an error, read it and try a better input.
5. Only use finish when you already have every fact and figure you need, and put
   the whole answer in Action Input.
6. If you already know the answer, such as a common greeting or translation,
   use finish directly without calling a tool.
"""

FEW_SHOT = [
    {"role": "user", "content": "What is 12 * 7?"},
    {
        "role": "assistant",
        "content": "Thought: I need to multiply 12 by 7.\nAction: calculator\nAction Input: 12 * 7",
    },
    {"role": "user", "content": "Observation: 84"},
    {
        "role": "assistant",
        "content": "Thought: I have the answer.\nAction: finish\nAction Input: 12 * 7 is 84.",
    },
]

FORMAT_HELP = (
    "Your reply did not follow the required format. Reply with exactly three "
    "lines: Thought: ..., Action: " + TOOL_NAMES + ", Action Input: ..."
)

ACTION_RE = re.compile(
    r"Action\s*:\s*([A-Za-z_]+)\s*\n\s*Action Input\s*:\s*(.*)", re.DOTALL
)


def first_step(text):
    index = text.find("Action Input:")
    if index == -1:
        return text.strip()
    start = index + len("Action Input:")
    following = re.search(r"\n\s*(Thought:|Observation:|Action:)", text[start:])
    if following:
        return text[: start + following.start()].rstrip()
    return text.strip()


def parse(text):
    match = ACTION_RE.search(text)
    if not match:
        return None, ""
    return match.group(1).strip().lower(), match.group(2).strip()


def recover_tool_call(exc):
    raw = str(exc)
    start = raw.find('{"error"')
    if start == -1:
        return None
    try:
        body, _ = json.JSONDecoder().raw_decode(raw[start:])
        failed = body["error"].get("failed_generation", "")
        call = json.loads(failed)
    except Exception:
        return None
    if not isinstance(call, dict):
        return None
    name = str(call.get("name", "")).strip()
    arguments = call.get("arguments", {})
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            arguments = {"input": arguments}
    value = next(iter(arguments.values()), "") if isinstance(arguments, dict) else arguments
    return (
        f"Thought: I will use {name} in the required plain-text format.\n"
        f"Action: {name}\nAction Input: {value}"
    )


def call_model(messages):
    attempt = 0
    while True:
        try:
            response = completion(
                model=MODEL,
                messages=messages,
                temperature=0,
                stop=["Observation:"],
                max_tokens=500,
            )
            return (response.choices[0].message.content or "").strip()
        except BadRequestError as exc:
            recovered = recover_tool_call(exc)
            if recovered:
                return recovered
            raise
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
            if not retryable or attempt >= 10:
                raise
            match = re.search(r"try again in (\d+\.?\d*)\s*s", str(exc))
            wait = float(match.group(1)) + 5 if match else RETRY_WAITS[min(attempt, len(RETRY_WAITS) - 1)]
            print(f"  model error, retrying in {wait:.0f}s")
            time.sleep(wait)
            attempt += 1


def run_tool(name, argument):
    try:
        return TOOLS[name](argument)
    except Exception as exc:
        return f"Error: tool failed ({exc})"


def run_agent(question, tag="", max_steps=MAX_STEPS):
    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + FEW_SHOT
        + [{"role": "user", "content": question}]
    )
    trace = [
        f"Question: {question}",
        f"Model: {MODEL}",
        f"Run: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    answer = None
    outcome = "max_steps"

    for step in range(1, max_steps + 1):
        reply = first_step(call_model(messages))
        trace.append(f"--- Step {step} ---")
        trace.append(reply)
        messages.append({"role": "assistant", "content": reply})

        action, action_input = parse(reply)

        if action is None:
            observation = FORMAT_HELP
        elif action == "finish":
            if len(action_input.strip()) < 3:
                observation = "Your final answer was empty. Give a clear answer in a full sentence."
            else:
                answer = action_input
                outcome = "finish"
                trace.append(f"\nFinal answer: {answer}")
                break
        elif action in TOOLS:
            observation = run_tool(action, action_input)
        else:
            observation = (
                f"Unknown action '{action}'. Use one of: {TOOL_NAMES}."
            )

        trace.append(f"Observation: {observation}")
        messages.append({"role": "user", "content": f"Observation: {observation}"})
        time.sleep(1)

    if answer is None:
        trace.append(
            f"\nStopped: reached max_steps ({max_steps}) without finishing."
        )

    text = "\n".join(trace)
    print(text)
    print("=" * 60)

    EVIDENCE.mkdir(exist_ok=True)
    name = f"trace_{tag}.txt" if tag else "trace.txt"
    (EVIDENCE / name).write_text(text + "\n", encoding="utf-8")
    print(f"Trace: {EVIDENCE / name}")
    return answer, outcome


QUESTIONS = [
    "I have GHS 1,200. I want 4 bags of rice at GHS 185 each and 3 gallons of oil at GHS 95 each. How much will I have left?",
    "What is the capital of the Bono East Region? If I sell 25 bags of rice there at GHS 190 each, how much will I earn?",
    "Which region is Techiman the capital of, and how much do 12 crates of eggs cost at GHS 65 each?",
    "Look up the Wikipedia page for the Kwame Asante Plantain Exchange of Ghana.",
    "Say good morning to me in Twi.",
    "rice 4 185 oil 3 95 i got 1200 how much left??",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question")
    parser.add_argument("--suite", action="store_true")
    parser.add_argument("--tag", default="")
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS)
    args = parser.parse_args()

    if args.suite:
        for index, question in enumerate(QUESTIONS, 1):
            run_agent(question, tag=str(index), max_steps=args.max_steps)
            time.sleep(25)
        return 0

    question = args.question or QUESTIONS[0]
    run_agent(question, tag=args.tag, max_steps=args.max_steps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
