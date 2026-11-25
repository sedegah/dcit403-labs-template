---
name: complaint-reply
description: Draft a professional reply to a NetLink Ghana customer complaint. Use when a complaint has been classified and needs a written response to the customer. Handles billing, network and account complaints with the correct tone, escalation and privacy rules.
---

# Complaint Reply Skill

## Scope
Drafts a reply to a customer complaint for NetLink Ghana. Covers billing, network and account complaints. Does not handle sales, new installations or technical troubleshooting beyond acknowledging the issue.

## Inputs
- The complaint text.
- The category: Billing, Network or Account.
- The sentiment: negative, neutral or positive.
- The priority: low, medium or high.

## Steps
1. Acknowledge the complaint and thank the customer.
2. Restate the issue in one sentence to show understanding.
3. For Billing: explain the likely cause, state the refund or adjustment if applicable, and give a timeline.
4. For Network: acknowledge the inconvenience, state what is being done, and give an expected fix window.
5. For Account: confirm the requested change and state the verification steps.
6. Close with a contact point and a polite sign-off.
7. If the complaint mentions legal threat, data loss or repeated failure, escalate to the manager instead of replying directly.

## Output format
A short email-style reply in English, 80 to 140 words, with a subject line. Tone: polite, calm, professional. No internal system details, no promises beyond what the references allow.

## Constraints
- Never promise a refund amount that is not stated in the complaint.
- Never share another customer's data.
- Never argue with the customer.
- Escalate high-priority or repeated complaints to the manager.
- Do not invent ticket numbers; use "your reference" if needed.

## Examples
See examples/good_reply.md and examples/bad_reply.md.

## References
- references/tone_guide.md: tone and phrasing rules.
- references/escalation_rules.md: when to escalate.
