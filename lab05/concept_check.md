# Lab 5: Beliefs and Memory: Retrieval (RAG): Concept Check

Answer in your own words before the Wednesday session (independent work). Your answers feed Section 2 of your lab report (Concept and classical root).

## Q1. Name the three sources of an LLM agent's beliefs and say which one can be wrong without anyone noticing.

_Your answer:_

The three sources are: (1) the model's parametric knowledge from training, (2) the conversation history or memory it carries, and (3) retrieved documents or tool results. Parametric knowledge can be wrong without anyone noticing, because it is baked into the weights and the model states it with the same confidence as a fact it just read. A retrieval result or a tool output, by contrast, can be checked against its source.

## Q2. Why do we use overlap when splitting text into chunks?

_Your answer:_

Overlap keeps a sentence or idea that straddles a chunk boundary from being split in two. Without overlap, a question whose answer sits across the split may match neither chunk well. A small overlap (for example 100 characters on a 500-character chunk) repeats the boundary text so each chunk still carries enough context to be retrieved and read on its own.

## Q3. The agent answers "The lab opens at 7am on Saturday" but no document says so. What is this failure called, and name two ways to reduce it.

_Your answer:_

This is **hallucination** (or confabulation): the model fills a gap with a plausible but unsupported statement. Two ways to reduce it: (1) instruct the model to answer only from the provided context and to say "I don't know" when the context is silent, and (2) require a citation for every claim so unsupported statements are visible, plus retrieve more and better chunks so the context actually contains the answer.

## Q4. Why must "What about Sunday?" be rewritten before retrieval?

_Your answer:_

The follow-up has no subject of its own; "what about Sunday" only makes sense next to the previous question about opening hours. A retriever embedding the bare phrase "What about Sunday?" would match documents about Sundays in general rather than the clinic's Sunday hours. Rewriting it to "What are the clinic's opening hours on Sunday?" produces a self-contained query that retrieves the right chunk.
