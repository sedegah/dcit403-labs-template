import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion

import chromadb

from embeddings import HashingEmbeddingFunction

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE / ".env")

MODEL = os.getenv("LLM_MODEL", "groq/openai/gpt-oss-20b")
DB = HERE / "db"
COLLECTION = "clinic_docs"
MEMORY = HERE / "memory.json"
EVIDENCE = HERE / "evidence"
TOP_K = 4
EMBEDDING = HashingEmbeddingFunction()

REWRITE_PROMPT = """You rewrite a follow-up question into a standalone question that can be
searched on its own. Use the conversation history to resolve pronouns and
elliptical phrases such as "What about Sunday?" or "And the pharmacy?".
Reply with only the rewritten question, nothing else."""

ANSWER_PROMPT = """You are the assistant of Asempa Community Clinic. Answer the user's
question using only the information in the provided context. If the context does
not contain the answer, say you do not know and suggest contacting the clinic.
Cite the source file name in square brackets after each fact, for example
[opening_hours.md]. Keep the answer concise and helpful."""


def load_memory():
    if MEMORY.exists():
        try:
            return json.loads(MEMORY.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"history": [], "facts": []}


def save_memory(memory):
    MEMORY.write_text(json.dumps(memory, indent=2, ensure_ascii=False), encoding="utf-8")


def completion_with_retry(messages, max_tokens):
    for wait in (2, 4, 8, 16, 32):
        try:
            return completion(model=MODEL, messages=messages, temperature=0, max_tokens=max_tokens)
        except Exception as exc:
            text = str(exc).lower()
            if "rate" not in text and "429" not in text and "timeout" not in text:
                raise
            print(f"  rate limit, waiting {wait}s")
            time.sleep(wait)
    return completion(model=MODEL, messages=messages, temperature=0, max_tokens=max_tokens)


def get_collection():
    client = chromadb.PersistentClient(path=str(DB))
    return client.get_collection(COLLECTION, embedding_function=EMBEDDING)


def rewrite_question(question, history):
    if not history:
        return question
    messages = [
        {"role": "system", "content": REWRITE_PROMPT},
        {
            "role": "user",
            "content": "History:\n"
            + "\n".join(f"Q: {item['q']}\nA: {item['a']}" for item in history[-4:])
            + f"\n\nFollow-up: {question}",
        },
    ]
    try:
        response = completion_with_retry(messages, 120)
        rewritten = (response.choices[0].message.content or "").strip()
        return rewritten or question
    except Exception:
        return question


import math
import re

# ... (existing imports)

def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def bm25_retrieve(question, k=TOP_K):
    collection = get_collection()
    all_data = collection.get(include=["documents", "metadatas"])
    documents = all_data["documents"]
    metadatas = all_data["metadatas"]
    pairs = list(zip(documents, metadatas))

    query_tokens = tokenize(question)
    if not query_tokens:
        return pairs[:k]

    # document lengths
    doc_tokens = [tokenize(doc) for doc, _ in pairs]
    lengths = [len(t) for t in doc_tokens]
    avgdl = sum(lengths) / len(lengths) if lengths else 1.0
    n = len(pairs)

    # document frequency
    df = {}
    for tokens in doc_tokens:
        for t in set(tokens):
            df[t] = df.get(t, 0) + 1

    k1 = 1.5
    b = 0.75
    scores = []
    for i, tokens in enumerate(doc_tokens):
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        score = 0.0
        for q in query_tokens:
            if q not in df:
                continue
            idf = math.log((n - df[q] + 0.5) / (df[q] + 0.5) + 1)
            f = tf.get(q, 0)
            denom = f + k1 * (1 - b + b * (lengths[i] / avgdl))
            score += idf * (f * (k1 + 1)) / denom if denom > 0 else 0.0
        scores.append(score)

    ranked = sorted(range(n), key=lambda i: scores[i], reverse=True)
    return [pairs[i] for i in ranked[:k]]


def answer_question(question, pairs, history):
    context = "\n\n".join(
        f"[{meta['source']}] {text}" for text, meta in pairs
    )
    messages = [
        {"role": "system", "content": ANSWER_PROMPT},
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        },
    ]
    response = completion_with_retry(messages, 400)
    return (response.choices[0].message.content or "").strip()


def run_one(question, memory, verbose=True):
    standalone = rewrite_question(question, memory["history"])
    if verbose and standalone != question:
        print(f"  rewritten: {standalone}")
    pairs = bm25_retrieve(standalone)
    answer = answer_question(standalone, pairs, memory["history"])
    memory["history"].append({"q": question, "a": answer})
    save_memory(memory)
    if verbose:
        print(f"Q: {question}")
        print(f"A: {answer}")
        print("  sources:", ", ".join(sorted({meta['source'] for _, meta in pairs})))
        print("-" * 60)
    return answer, pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question")
    parser.add_argument("--suite", action="store_true")
    args = parser.parse_args()

    EVIDENCE.mkdir(exist_ok=True)
    memory = load_memory()

    if args.suite:
        questions = [
            "What are the opening hours of the OPD?",
            "What about Sunday?",
            "Do I need an appointment for the laboratory?",
            "Is the lipid profile covered by NHIS?",
            "How do I prepare for a fasting blood sugar test?",
            "Can I pay by card?",
            "Where should I go in an emergency?",
            "What services does the clinic not provide?",
        ]
        lines = ["# Lab 5 RAG Results", "", f"Model: `{MODEL}`", ""]
        for question in questions:
            print(f"\n=== {question} ===")
            answer, pairs = run_one(question, memory, verbose=True)
            lines.append(f"## {question}")
            lines.append("")
            lines.append(answer)
            lines.append("")
            lines.append("Sources: " + ", ".join(sorted({meta["source"] for _, meta in pairs})))
            lines.append("")
        (EVIDENCE / "results.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"\nResults written to {EVIDENCE / 'results.md'}")
        return 0

    if args.question:
        run_one(args.question, memory, verbose=True)
        return 0

    print("Usage: python rag_agent.py --question \"...\"  or  --suite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
