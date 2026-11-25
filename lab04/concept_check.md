# Lab 4: Defined Workflows and Reusable Agent Skills (SKILL.md): Concept Check

Answer in your own words before the Wednesday session (independent work). Your answers feed Section 2 of your lab report (Concept and classical root).

## Q1. A bank wants every loan enquiry classified as personal, business or mortgage and answered by a specialist template. Which pattern is this? Workflow or agent?

_Your answer:_

This is a **workflow**, specifically a routing (classification) pattern. The set of categories is fixed, the path from input to a specialist template is deterministic, and every enquiry follows the same steps. There is no open-ended planning or tool choice, so an agent would add cost and unpredictability for no benefit.

## Q2. Name the five workflow patterns and give a one-line Ghanaian business example of each.

_Your answer:_

1. **Prompt chaining** - a loan application is first checked for completeness, then scored, then a decision letter is drafted.
2. **Routing** - a customer message is classified as billing, network or account and sent to the matching specialist queue.
3. **Parallel** - a new merchant's documents are checked for identity, address and business registration at the same time.
4. **Orchestrator-worker** - a manager agent splits a market research task into price, competitor and demand sub-tasks for worker agents.
5. **Evaluator-optimizer** - a drafted complaint reply is scored for tone and completeness, then rewritten until it passes.

## Q3. Why is the `description` field the most important line in a SKILL.md?

_Your answer:_

The description is the only part of the skill that is always loaded. The system uses it to decide whether the skill is relevant to the current task, so a vague description means the skill is never triggered even if its body is perfect. It must say both what the skill does and when to use it, in the language a router can match against.

## Q4. Should "look up a customer's balance" be a skill or a tool? Why?

_Your answer:_

It should be a **tool**. Looking up a balance is a single, well-defined action with a clear input and output, backed by a database. A skill is a reusable bundle of instructions and references for a whole task, such as replying to a complaint. Skills orchestrate; tools execute.
