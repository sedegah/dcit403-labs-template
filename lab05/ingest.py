import argparse
import os
import re
import sys
from pathlib import Path

import chromadb

from embeddings import HashingEmbeddingFunction

HERE = Path(__file__).resolve().parent
DOCS = HERE / "docs"
DB = HERE / "db"
COLLECTION = "clinic_docs"
EMBEDDING = HashingEmbeddingFunction()


def load_documents():
    documents = []
    for path in sorted(DOCS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        documents.append((path.name, text))
    return documents


def chunk_text(text, size, overlap):
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    step = max(1, size - overlap)
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += step
    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--overlap", type=int, default=100)
    args = parser.parse_args()

    documents = load_documents()
    if not documents:
        raise SystemExit(f"No markdown documents found in {DOCS}")

    DB.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=str(DB))

    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass

    collection = client.create_collection(COLLECTION, embedding_function=EMBEDDING)

    ids = []
    texts = []
    metadatas = []

    for filename, text in documents:
        for index, chunk in enumerate(chunk_text(text, args.chunk_size, args.overlap)):
            ids.append(f"{filename}::chunk_{index}")
            texts.append(chunk)
            metadatas.append({"source": filename, "chunk": index})

    collection.add(ids=ids, documents=texts, metadatas=metadatas)

    lengths = [len(chunk) for chunk in texts]
    print(f"Documents: {len(documents)}")
    print(f"Chunk size: {args.chunk_size}, overlap: {args.overlap}")
    print(f"Chunks: {len(texts)}")
    print(f"Average chunk length: {sum(lengths) // len(lengths)} characters")
    print(f"Stored in: {DB}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
