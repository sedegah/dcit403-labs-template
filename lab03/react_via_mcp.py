import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
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

MODEL = os.getenv(
    "REACT_MODEL",
    os.getenv("LAB2_MODEL", "groq/qwen/qwen3.8-27b"),
)
EVIDENCE = HERE / "evidence"
MAX_STEPS = 6
RETRY_WAITS = (5, 10, 20, 30)

SERVER = StdioServerParameters(
    command=sys.executable,
    args=[str(HERE / "server.py")],
    cwd=str(HERE),
)

PROMPT = """You are the stock assistant of a community pharmacy in Accra, Ghana.

Your tools are provided by an MCP server. You know only this list:

{tools}

Work in steps. On every step reply with exactly this and nothing else:

Thought: <one or two sentences of reasoning>
Action: <one tool name from the list, or finish>
Action Input: <a JSON object of arguments, or the final answer for finish>

Rules:
1. Arguments must be a JSON object, for example {{"item": "amoxicillin", "strength": "500mg"}}.
   Use only the argument names shown for that tool.
2. Never invent stock, prices or dates: call a tool and use what it returns.
3. Never write an Observation line; the system runs the tool and sends it back.
4. If a sale is refused, relay the refusal exactly and do not retry with a different quantity.
5. Finish with Action: finish and put the whole answer in Action Input.
"""


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


def render_tools(tools):
    blocks = []
    for tool in tools:
        schema = tool.inputSchema or {}
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        arguments = []
        for name, spec in properties.items():
            kind = spec.get("type", "string")
            default = f", default {spec['default']!r}" if "default" in spec else ""
            optional = "" if name in required else " (optional)"
            arguments.append(f"      - {name}: {kind}{default}{optional}")
        blocks.append(
            f"  {tool.name}\n"
            f"    {tool.description or ''}\n"
            f"    arguments:\n"
            + ("\n".join(arguments) if arguments else "      (none)")
        )
    return "\n\n".join(blocks)


def content_text(result):
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


def parse(reply):
    action_match = re.search(r"^\s*Action\s*:\s*(.+?)\s*$", reply, re.I | re.M)
    if not action_match:
        return None, ""
    action = action_match.group(1).strip().strip("`").strip()
    input_match = re.search(r"^\s*Action Input\s*:\s*(.*)$", reply, re.I | re.M | re.S)
    payload = input_match.group(1).strip() if input_match else ""
    if payload.startswith("```"):
        payload = payload.strip("`").strip()
        if payload.lower().startswith("json"):
            payload = payload[4:].strip()
    return action, payload


def parse_arguments(payload):
    try:
        return json.loads(payload or "{}")
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", payload, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


async def model_call(messages):
    for wait in (*RETRY_WAITS, None):
        try:
            response = await acompletion(
                model=MODEL,
                messages=messages,
                temperature=0,
                stop=["Observation:"],
            )
            return (response.choices[0].message.content or "").strip()
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


async def run(question):
    require_key()
    EVIDENCE.mkdir(exist_ok=True)
    lines = [
        "# Lab 2 ReAct agent with tools discovered from the MCP server",
        f"# model: {MODEL}",
        f"# run: {datetime.now().isoformat(timespec='seconds')}",
        f"# question: {question}",
        "",
    ]

    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            names = [tool.name for tool in tools]
            print(f"Discovered over MCP: {', '.join(names)}")

            lines.append("DISCOVERED TOOLS (from the server, not imported):")
            lines.append(render_tools(tools))
            lines.append("")

            messages = [
                {"role": "system", "content": PROMPT.format(tools=render_tools(tools))},
                {"role": "user", "content": question},
            ]
            lines.append(f"QUESTION: {question}")
            lines.append("-" * 70)

            answer = None
            outcome = "max_steps"
            for step in range(1, MAX_STEPS + 1):
                started = time.perf_counter()
                reply = await model_call(messages)
                elapsed = time.perf_counter() - started
                messages.append({"role": "assistant", "content": reply})
                lines.append(f"\nSTEP {step} ({elapsed:.2f}s)\n{reply}")

                action, payload = parse(reply)
                if action is None:
                    observation = (
                        "Could not parse your reply. Use exactly:\n"
                        "Thought: ...\n"
                        f"Action: {names} or finish\n"
                        'Action Input: {"..."} or the final answer'
                    )
                    lines.append("  [parser] unparseable reply -> corrective Observation")
                elif action.lower() == "finish":
                    answer = payload or "No answer given."
                    outcome = "finish"
                    break
                elif action not in names:
                    observation = f"Unknown action '{action}'. Valid actions are {names}, or finish."
                    lines.append("  [unknown tool] corrective Observation")
                else:
                    try:
                        arguments = parse_arguments(payload)
                        if not isinstance(arguments, dict):
                            raise ValueError("arguments must be a JSON object")
                    except (json.JSONDecodeError, ValueError) as exc:
                        observation = (
                            f"Action Input for {action} must be a JSON object of named "
                            f"arguments ({exc})."
                        )
                        lines.append("  [bad arguments] corrective Observation")
                    else:
                        result = await session.call_tool(action, arguments)
                        observation = content_text(result)
                        lines.append(
                            f"  [mcp] {action}({arguments}) -> "
                            f"{' '.join(observation.split())[:200]}"
                        )
                        if result.isError:
                            observation = f"Tool error: {observation}"

                if len(observation) > 1500:
                    observation = observation[:1500] + " ...[truncated]"
                lines.append(f"Observation: {observation}")
                messages.append({"role": "user", "content": f"Observation: {observation}"})

            lines.append("\n" + "=" * 70)
            lines.append(f"OUTCOME: {outcome}")
            lines.append(f"FINAL ANSWER: {answer}")
            print(f"\n{answer}")

    out = EVIDENCE / "react_via_mcp.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nTrace: {out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", default="Do we have amoxicillin 500mg?")
    args = parser.parse_args()
    asyncio.run(run(args.question))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
