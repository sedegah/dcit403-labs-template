# Lab 12: Deployment and Observability: Concept Check

Answer in your own words before the Wednesday session (independent work). Your answers feed Section 2 of your lab report (Concept and classical root).

## Q1. Give one advantage and one disadvantage of Telegram compared with a web front-end for your problem owner.

_Your answer:_

Advantage: Telegram needs no installation beyond the app and gives push notifications, so users get replies instantly. Disadvantage: it is tied to one messaging platform and offers less control over layout and branding than a web front-end.

## Q2. What is the difference between a log and a trace?

_Your answer:_

A log is a record of discrete events (a request arrived, a tool was called). A trace links those events across a single request so you can follow the whole path from input to output and see where time was spent.

## Q3. Why should the log store a hashed chat ID rather than the raw one?

_Your answer:_

Hashing the chat ID lets you correlate messages from the same user without storing a directly identifying value, supporting the data-protection principle of not keeping raw personal identifiers longer than needed.

## Q4. Name three metrics you would watch for your team system after launch.

_Your answer:_

Request latency (p95), error rate, and token cost per request.
