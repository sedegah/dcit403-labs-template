# Lab 8: Architectural Design and AUML Interaction Diagrams: Concept Check

Answer in your own words before the Wednesday session (independent work). Your answers feed Section 2 of your lab report (Concept and classical root).

## Q1. Two functionalities both read and write the orders table and run one after the other. Should they be in the same agent? Why?

_Your answer:_

Yes, they should be in the same agent. They share mutable state and run sequentially, so splitting them would create a race condition and a handoff for no benefit. An agent should own a coherent piece of state; co-located read/write access keeps the data consistent.

## Q2. List the eight fields of a Prometheus agent descriptor.

_Your answer:_

1. Name
2. Type
3. Responsibilities (description)
4. Percepts
5. Actions
6. Goals
7. Protocols
8. Characteristics (cardinality, concurrency, etc.)

## Q3. Which AUML fragment would you use for "if the rider is not free, try the next rider up to three times"?

_Your answer:_

A loop fragment (with a guard) combined with an alt fragment: loop(3) { alt { rider available -> assign } { else -> try next rider } }. The loop bounds the retries and the alt handles the condition.

## Q4. What is the difference between a system overview diagram and an interaction diagram?

_Your answer:_

A system overview diagram shows the agents, their responsibilities and how they relate at a high level, without message detail. An interaction diagram shows the actual messages exchanged between agents in a specific scenario, in time order.
