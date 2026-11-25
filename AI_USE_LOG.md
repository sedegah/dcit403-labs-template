# AI-Use Log

Add one row every time you use an AI tool for lab work (see Lab Manual Section 4).
Copy the rows for each lab into that lab's report.

| Date | Lab | Tool | What I asked | What I used | What I changed or checked |
|---|---|---|---|---|---|
| 2026-11-25 | 3 | OpenCode (DeepSeek V4.1 Flash) | Scaffold and test the Lab 3 MCP server, client agent and ReAct-via-MCP trace; draft concept-check answers | `server.py`, `function_calling.py`, `client_agent.py`, `react_via_mcp.py`, `concept_check.md` | Tested all four MCP tools over stdio, checked stock arithmetic and the oversell/expiry refusals, and reviewed the generated trace and answers |
| 2026-11-25 | 2 | OpenCode (DeepSeek V4.1 Flash) | Build the ReAct agent and baseline, run the six questions, and draft the concept check | `tools.py`, `react_agent.py`, `baseline.py`, `concept_check.md` | Safe calculator and Wikipedia lookup, tolerant parser, error handling, six traces, baseline comparison, and the four concept-check answers |
| 2026-11-25 | 4 | OpenCode (DeepSeek V4.1 Flash) | Build the LangGraph complaint workflow, skill, tests and evidence | `workflow.py`, `n8n_workflow.json`, `skills/complaint-reply/*`, `tests/complaints.md`, `concept_check.md` | LangGraph graph with classify, sentiment, draft, evaluate, finalize; skill with references and examples; eight test complaints; before/after evidence |
| 2026-11-25 | 5 | OpenCode (DeepSeek V4.1 Flash) | Build the RAG ingest and agent, tests and evidence | `ingest.py`, `rag_agent.py`, `embeddings.py`, `notes.md`, `concept_check.md` | ChromaDB with hashing embeddings, BM25 retrieval, question rewriting, memory, ten test questions, results and chunking evidence |
| 2026-11-25 | 6 | OpenCode (DeepSeek V4.1 Flash) | Write the Prometheus spec, tools stub and scenario check | `spec.md`, `tools_stub.py`, `scenario_check.py`, `concept_check.md` | Goal hierarchy, scenarios, percepts/actions mapped to tools, agent descriptors, scenario check passes |
| 2026-11-25 | 7 | OpenCode (DeepSeek V4.1 Flash) | Build the multi-agent orchestrator with venue and catering agents | `orchestrator.py`, `agent_cards.json`, `notes.md`, `concept_check.md` | FIPA-ACL messages, agent cards, venue/catering handoff, messages.jsonl evidence |
| 2026-11-25 | 8 | OpenCode (DeepSeek V4.1 Flash) | Design the QuickBite architecture and generate the sequence diagram | `design.md`, `agents.py`, `concept_check.md`, `evidence/messages.jsonl`, `evidence/generated_sequence.md` | Agent descriptors, agent classes, AUML sequence diagram from the message log |
| 2026-11-25 | 9 | OpenCode (DeepSeek V4.1 Flash) | Build the refund workflow with eligibility, approval and traces | `refund_graph.py`, `concept_check.md` | LangGraph refund graph, five traces, manual_refunds.csv |
| 2026-11-25 | 10 | OpenCode (DeepSeek V4.1 Flash) | Build the eval suite for the FAQ agent | `evals/cases.jsonl`, `evals/run.py`, `concept_check.md` | 12 test cases, model-graded checks, eval_results.md |
| 2026-11-25 | 11 | OpenCode (DeepSeek V4.1 Flash) | Red-team the vulnerable agent and add guardrails | `guardrail.py`, `redteam.md`, `concept_check.md` | Five attacks before and after, guardrail code blocking IDOR and exfiltration |
| 2026-11-25 | 12 | OpenCode (DeepSeek V4.1 Flash) | Create the deployment workflow and sanitised log sample | `workflow.json`, `concept_check.md` | n8n workflow, log sample with hashed chat IDs |
