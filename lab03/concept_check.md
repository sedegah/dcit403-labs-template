# Lab 3: Percepts and Actions as Tools: Function Calling and MCP: Concept Check

Answer in your own words before the Wednesday session (independent work). Your answers feed Section 2 of your lab report (Concept and classical root).

## Q1. List one advantage and one disadvantage of native function calling compared with the Lab 2 text protocol.

_Your answer:_

Native function calling returns a structured `tool_calls` field whose arguments are checked against a JSON schema. The client does not have to parse free text such as "Action:" and "Action Input:", so malformed replies and ambiguous tool names are much less common, and one turn can contain several tool calls.

The disadvantage is that it depends on the model provider supporting the same tool-calling API and schema conventions. The exchange is less transparent than a written ReAct trace, and when a call fails it can be harder to see whether the model chose the wrong tool, produced invalid arguments, or the provider silently changed the format. It also adds schema tokens to every request.

## Q2. In MCP, what is the difference between a tool and a resource? Give a pharmacy example of each.

_Your answer:_

A tool is an action the model may ask the server to perform. It has named arguments, can change state, and its result is returned as an observation. `record_sale(item="Paracetamol", strength="500mg", qty=3)` is a tool because it changes the stock file and can refuse an invalid sale.

A resource is read-only data addressed by a URI. It supplies context rather than performing an action. `stock://all` is a resource: it returns the current stock table so the model can read it, but it cannot modify anything. In short, a tool does something; a resource is something the agent can look at.

## Q3. Why should `record_sale` check the quantity even though the system prompt already says "never oversell"?

_Your answer:_

A prompt is guidance to the model, not a guarantee about the program's behaviour. The model can misread the stock, be manipulated by a user, receive a stale quantity, or simply make a mistake. If the only protection is the sentence "never oversell", an invalid sale can still reach the data.

`record_sale` must enforce the rule in code because code is the source of truth for the stock file. It can reject a non-positive quantity, an expired batch, an ambiguous product, or a quantity larger than the stock on hand, and it can return a clear refusal. That is defence in depth: the prompt states the policy, and the tool enforces it.

## Q4. Which messages in the worked example are percepts?

_Your answer:_

The percepts are the messages the agent receives from outside itself: the user's question and each Observation returned by the MCP server, such as the stock rows, the sale receipt, or the refusal message. If the agent reads the `stock://all` resource, that data is also a percept.

The assistant's Thought and Action lines are not percepts. They are the agent's internal reasoning and the actions it chooses; the resulting tool output comes back as the next percept.
