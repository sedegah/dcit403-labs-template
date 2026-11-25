# AI-Use Log

Add one row every time you use an AI tool for lab work (see Lab Manual Section 4).
Copy the rows for each lab into that lab's report.

| Date | Lab | Tool | What I asked | What I used | What I changed or checked |
|---|---|---|---|---|---|
| 2026-11-25 | 3 | OpenCode (DeepSeek V4.1 Flash) | Scaffold and test the Lab 3 MCP server, client agent and ReAct-via-MCP trace; draft concept-check answers | `server.py`, `function_calling.py`, `client_agent.py`, `react_via_mcp.py`, `concept_check.md` | Tested all four MCP tools over stdio, checked stock arithmetic and the oversell/expiry refusals, and reviewed the generated trace and answers |
| 2026-11-25 | 2 | OpenCode (DeepSeek V4.1 Flash) | Build the ReAct agent and baseline, run the six questions, and draft the concept check | `tools.py`, `react_agent.py`, `baseline.py`, `concept_check.md` | Safe calculator and Wikipedia lookup, tolerant parser, error handling, six traces, baseline comparison, and the four concept-check answers |
| 2026-11-25 | 4 | OpenCode (DeepSeek V4.1 Flash) | Build the LangGraph complaint workflow, skill, tests and evidence | `workflow.py`, `n8n_workflow.json`, `skills/complaint-reply/*`, `tests/complaints.md`, `concept_check.md` | LangGraph graph with classify, sentiment, draft, evaluate, finalize; skill with references and examples; eight test complaints; before/after evidence |
| 2026-11-25 | 5 | OpenCode (DeepSeek V4.1 Flash) | Build the RAG ingest and agent, tests and evidence | `ingest.py`, `rag_agent.py`, `embeddings.py`, `notes.md`, `concept_check.md` | ChromaDB with hashing embeddings, BM25 retrieval, question rewriting, memory, ten test questions, results and chunking evidence |
