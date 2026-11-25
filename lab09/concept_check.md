# Lab 9: Dynamic Workflows: Failure Handling and Human Approval: Concept Check

Answer in your own words before the Wednesday session (independent work). Your answers feed Section 2 of your lab report (Concept and classical root).

## Q1. Why is retrying a payment call dangerous unless the call is idempotent? What does idempotent mean?

_Your answer:_

Idempotent means calling the same operation twice has the same effect as calling it once. Retrying a payment call that is not idempotent can charge the customer twice. The fix is an idempotency key so the provider recognises the retry as the same request.

## Q2. Give one example each of a transient and a permanent failure in your team system.

_Your answer:_

Transient: a timeout calling the payment provider; retrying after a short wait usually succeeds. Permanent: an invalid account number or an expired card; retrying will never succeed and the request must be rejected or corrected.

## Q3. Name four conditions that should trigger human approval.

_Your answer:_

Refund amount above a threshold, a customer threatening legal action, a third repeat complaint on the same issue, and any request involving data privacy or compensation above policy limits.

## Q4. Map "approver rejects the refund" to a BDI term.

_Your answer:_

It is a change in the agent's beliefs (the approval was denied) that causes it to drop its intention (process the refund) and adopt a new one (reject the request and inform the customer).
