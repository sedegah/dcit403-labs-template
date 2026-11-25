# Lab 5 Notes

Approach: load the six clinic markdown documents, split each into overlapping character chunks, embed them with ChromaDB's default sentence-transformer model, and store them in a persistent ChromaDB collection. At query time, rewrite follow-up questions into standalone questions using the conversation history, retrieve the top-4 chunks, and generate an answer that cites the source file. Conversation turns are appended to memory.json so follow-ups can be resolved.

Chunking: 500 characters with 100 characters of overlap. See evidence/chunking.md.

Limitations: the embedding model is small and English-only; very short or very long answers may be missed; no reranking is applied.
