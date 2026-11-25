# Lab 2: Architectures: A ReAct Agent From Scratch: Concept Check

Answer in your own words before the Wednesday session (independent work). Your answers feed Section 2 of your lab report (Concept and classical root).

## Q1. Classify a thermostat, a chess engine and a ReAct agent as reactive, deliberative or hybrid, with one reason each.

_Your answer:_

A thermostat is **reactive**. It senses the current temperature and switches the heater on or off from a fixed threshold. It holds no model of the room, plans nothing, and cannot consider what will happen later.

A chess engine is **deliberative**. Before it moves it searches possible future positions, evaluates them, and chooses the branch with the best expected outcome. It maintains an internal model of the board and reasons ahead.

A ReAct agent is **hybrid**. It reacts to each Observation as it arrives, but the Thought before each Action is deliberation about what the observation means and what to do next. It interleaves reactive feedback with forward planning rather than doing only one.

## Q2. In the trace above, which lines are percepts, and which are actions?

_Your answer:_

The percepts are everything the agent receives from outside itself. That includes the user's question and every `Observation:` line: a calculator result, a Wikipedia extract, a tool error, or a corrective message from the harness. They are the inputs the agent did not generate.

The actions are the `Action:` and `Action Input:` pairs the agent emits. They name a tool and supply its argument, for example `Action: calculator` with `Action Input: 25 * 190`. Choosing `finish` is also an action because it ends the episode. The `Thought:` lines are neither: they are the agent's internal reasoning, not an input and not an effect on the world.

## Q3. Why do we pass `stop=["Observation:"]` when calling the model?

_Your answer:_

`stop=["Observation:"]` tells the model provider to end generation as soon as it would produce the token sequence `Observation:`. In the ReAct protocol the Observation must come from the program that actually ran the tool, not from the model.

Without the stop sequence a model can keep writing the whole trajectory in one reply: it invents a plausible tool result, continues with another Thought, and may even fabricate the final answer. The loop would then never execute the real tool, and the invented observation would enter the context as if it were true. Stopping generation hands control back to the program, which runs the action and appends a genuine observation.

## Q4. Map the trace above to the BDI terms belief, desire and intention.

_Your answer:_

**Beliefs** are what the agent takes to be true about the world at a given moment: the user's question, the calculator result, the Wikipedia extract, the stock quantity, or an error message. Each Observation updates them, and the next Thought is based on the updated set.

**Desires** are the goals the agent is trying to satisfy: answer the trader's budget question, find the capital of Bono East, or complete a sale without overselling. They come from the user and stay fixed for the episode.

**Intentions** are the commitments the agent adopts to reach those desires: the specific action it chooses next, such as `calculator` with `25 * 190`, and the ordered plan of steps it is pursuing. A failed observation can force it to drop an intention and choose another, which is the deliberation visible between steps.
