# Lab 7: Multi-Agent Systems: Orchestration, Roles and Handoffs: Concept Check

Answer in your own words before the Wednesday session (independent work). Your answers feed Section 2 of your lab report (Concept and classical root).

## Q1. Give two good reasons and one bad reason to split a system into multiple agents.

_Your answer:_

Good reasons: (1) different components need different expertise or data sources, such as a venue agent and a catering agent; (2) components can be developed and deployed independently by different teams. Bad reason: splitting a single simple task into agents just to use the word "multi-agent", which adds message-passing overhead and failure points without any benefit.

## Q2. Which performative should the Venue Agent use when no venue fits the budget? Why not `failure`?

_Your answer:_

The Venue Agent should use `refuse`. `refuse` means "I understood your request but I cannot do it", which is honest here: the agent understood the request but no venue satisfies the constraints. `failure` means something went wrong during processing, which implies a fault rather than a legitimate "no match".

## Q3. What does an A2A agent card contain, and what classical idea does it replace?

_Your answer:_

An A2A agent card contains the agent's name, description, URL, skills, and authentication details. It replaces the FIPA directory facilitator / yellow pages: instead of registering with a central directory, an agent publishes a card at a well-known URL that others can fetch to discover its capabilities.

## Q4. What context must the Venue Agent pass to the Catering Agent in the handoff?

_Your answer:_

The Venue Agent must pass the chosen venue's constraints (kitchen access, open-flame policy, outdoor space) and the remaining budget, along with the guest count. The Catering Agent needs these to filter caterers by their requirements and to stay within budget.
