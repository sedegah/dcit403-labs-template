import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from litellm import acompletion
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE / ".env")

MODEL = os.getenv("LLM_MODEL", "groq/openai/gpt-oss-20b")
LOG = HERE / "evidence" / "tool_calls.jsonl"
EVIDENCE = HERE / "evidence"
MAX_STEPS = 8
PAUSE_SECONDS = 8
RETRY_WAITS = (5, 10, 20, 30)

SERVER = StdioServerParameters(
    command=sys.executable,
    args=[str(HERE / "server.py")],
    cwd=str(HERE),
)

SYSTEM_PROMPT = """You are the stock assistant of a community pharmacy in Accra, Ghana.
Learn about stock only by calling the tools you are given. Never invent a quantity,
price or expiry date, and never guess whether an item is in stock.

Use check_stock for a named medicine and strength, search_items when you only have
part of a name or want to know which forms exist, and list_expiring for questions
about expiry. Use record_sale only when the user clearly asks to sell or remove
stock; pass the exact strength whenever more than one strength exists.

Never oversell. If record_sale refuses a sale, relay the reason exactly and do not
retry with a different quantity. Answer with the figures the tools returned.
"""

SIX_QUESTIONS = [
    "Do we have amoxicillin 500mg?",
    "Which items expire within 60 days?",
    "Do you have any paracetamol syrup, and what does it cost?",
    "How much paracetamol do we have?",
    "Record a sale of 3 packs of amoxicillin 500mg.",
    "Sell 500 packs of paracetamol 500mg to a customer.",
]


def require_key():
    prefix = MODEL.split("/", 1)[0]
    needed = {
        "groq": "GROQ_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }.get(prefix)
    if needed and not os.getenv(needed):
        raise SystemExit(
            f"{needed} is not set. Add it to {HERE.parent / '.env'} or the environment, "
            "then run this script again."
        )


def tool_schemas(tools):
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema or {"type": "object", "properties": {}},
            },
        }
        for tool in tools
    ]


def result_text(result):
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        if isinstance(structured, dict) and set(structured) == {"result"}:
            structured = structured["result"]
        return json.dumps(structured, ensure_ascii=False)
    parts = []
    for block in result.content or []:
        text = getattr(block, "text", None)
        if text is not None:
            parts.append(text)
    return "\n".join(parts)


def summarise(text, limit=300):
    return " ".join(text.split())[:limit]


def value(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def assistant_message(message, step=0):
    out = {"role": "assistant", "content": message.content or ""}
    calls = getattr(message, "tool_calls", None)
    if calls:
        out["tool_calls"] = [
            {
                "id": value(call, "id") or f"call_{step}_{index}",
                "type": "function",
                "function": {
                    "name": value(value(call, "function"), "name"),
                    "arguments": value(value(call, "function"), "arguments") or "{}",
                },
            }
            for index, call in enumerate(calls, 1)
        ]
    return out


def log_call(question_id, question, name, args, summary, duration_ms, ok):
    LOG.parent.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "question_id": question_id,
        "question": question,
        "tool": name,
        "arguments": args,
        "result_summary": summary,
        "duration_ms": duration_ms,
        "ok": ok,
        "model": MODEL,
    }
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


async def chat(messages, schemas):
    for wait in (*RETRY_WAITS, None):
        try:
            return await acompletion(
                model=MODEL,
                messages=messages,
                tools=schemas,
                temperature=0,
            )
        except Exception as exc:
            text = f"{type(exc).__name__}: {exc}".lower()
            retryable = any(
                marker in text
                for marker in ("rate limit", "ratelimit", "429", "connection", "timeout", "overloaded")
            )
            if not retryable or wait is None:
                raise
            print(f"  retrying in {wait}s after {type(exc).__name__}")
            await asyncio.sleep(wait)


async def answer(session, schemas, question, question_id, transcript):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    transcript.append("=" * 72)
    transcript.append(f"QUESTION {question_id}: {question}")

    for step in range(1, MAX_STEPS + 1):
        response = await chat(messages, schemas)
        message = response.choices[0].message
        messages.append(assistant_message(message, step))
        transcript.append(f"\n[step {step}] assistant: {message.content!r}")

        calls = getattr(message, "tool_calls", None)
        if not calls:
            final = message.content or "(no answer)"
            transcript.append(f"FINAL: {final}")
            return final

        for index, call in enumerate(calls, 1):
            name = value(value(call, "function"), "name")
            raw_args = value(value(call, "function"), "arguments") or "{}"
            call_id = value(call, "id") or f"call_{step}_{index}"
            transcript.append(f"[step {step}] tool_call: {name}({raw_args})")

            args = {}
            text = ""
            ok = False
            duration_ms = 0
            try:
                args = json.loads(raw_args)
                if not isinstance(args, dict):
                    raise ValueError("arguments must be a JSON object")
            except (json.JSONDecodeError, ValueError) as exc:
                text = f"Invalid arguments for {name}: {exc}"
                transcript.append(f"          -> {text}")
            else:
                started = time.perf_counter()
                try:
                    result = await session.call_tool(name, args)
                    text = result_text(result)
                    ok = not result.isError
                except Exception as exc:
                    text = f"Tool error: {type(exc).__name__}: {exc}"
                duration_ms = int((time.perf_counter() - started) * 1000)
                transcript.append(f"          -> {summarise(text)} ({duration_ms} ms)")

            log_call(question_id, question, name, args, summarise(text), duration_ms, ok)
            messages.append({"role": "tool", "tool_call_id": call_id, "content": text})

    transcript.append(f"OUTCOME: max_steps ({MAX_STEPS}) reached")
    return "Stopped: the agent did not finish within the step limit."


async def run(questions, tag):
    require_key()
    EVIDENCE.mkdir(exist_ok=True)
    transcript = [
        f"# client_agent.py on {MODEL}",
        f"# server: python {HERE / 'server.py'}",
        f"# run: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]

    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            schemas = tool_schemas(tools)
            names = ", ".join(tool.name for tool in tools)
            transcript.append(f"DISCOVERED TOOLS: {names}")
            print(f"Discovered tools: {names}")

            for index, question in enumerate(questions, 1):
                print(f"\n[{index}/{len(questions)}] {question}")
                if index > 1:
                    await asyncio.sleep(PAUSE_SECONDS)
                try:
                    final = await answer(session, schemas, question, index, transcript)
                except Exception as exc:
                    final = f"ERROR: {type(exc).__name__}: {exc}"
                    transcript.append(f"ERROR: {final}")
                print(f"  -> {final}")

    out = EVIDENCE / f"client_agent_{tag}.txt"
    out.write_text("\n".join(transcript), encoding="utf-8")
    print(f"\nTranscript: {out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", action="append", default=[])
    parser.add_argument("--suite", action="store_true")
    parser.add_argument("--tag", default="")
    args = parser.parse_args()

    questions = list(args.question)
    if args.suite:
        questions += SIX_QUESTIONS
    if not questions:
        questions = SIX_QUESTIONS[:1]

    tag = args.tag or ("suite" if args.suite else "run")
    asyncio.run(run(questions, tag))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
