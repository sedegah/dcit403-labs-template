# Lab 6: Prometheus System Specification for AI Agents: Concept Check

Answer in your own words before the Wednesday session (independent work). Your answers feed Section 2 of your lab report (Concept and classical root).

## Q1. Name the three Prometheus phases and one artefact from each.

_Your answer:_

1. **System specification** produces the goal hierarchy, scenarios, and the mapping of percepts and actions to tools.
2. **Architectural design** produces the agent grouping, the agent descriptors, and the interaction overview.
3. **Detailed design** produces the capability descriptors, the data structures, and the process diagrams.

## Q2. Rewrite "Booking screen" as a goal.

_Your answer:_

"Allow a patient to book an appointment for a chosen service on an available day." A goal states what is achieved, not the interface used to achieve it.

## Q3. Which question do you ask to move down a goal hierarchy, and which to move up?

_Your answer:_

Moving down, ask "how?" to break a goal into sub-goals. Moving up, ask "why?" to find the parent goal that justifies a sub-goal. You stop going up when you reach the system goal.

## Q4. Why must "patient mentions chest pain" appear as a scenario, not just a rule in the prompt?

_Your answer:_

A scenario is a concrete, testable path through the system: it names the trigger, the percepts, the actions and the outcome. A rule buried in a prompt is only guidance to the model and cannot be traced, tested or assigned to an agent. Making chest pain a scenario forces the system to define the redirect-to-emergency action and to verify it happens every time.
