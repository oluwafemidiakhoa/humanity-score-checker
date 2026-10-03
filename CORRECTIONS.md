# Corrections and Appeals Policy

Humanity Score accepts evidence-backed corrections to published audits.

## Principles

- Payment cannot buy a correction.
- A commercial customer receives no scoring advantage over a non-customer.
- Negative evidence is not removed because it is inconvenient.
- New evidence can change a score only through the published methodology.
- Historical receipts remain immutable; corrected or re-audited results receive a new report hash.

## What to submit

A correction request should include:

- product name
- report hash being challenged
- specific factual claim being challenged
- source URLs or preserved evidence
- requested correction
- identity or organization of the submitter

The `create_appeal` MCP tool can generate a deterministic appeal intake record.

## Review process

1. Intake is recorded against the report hash.
2. Submitted evidence is checked for relevance and provenance.
3. If the dispute concerns reviewer coding, an independent second coding pass should be performed.
4. Reviewer disagreement is recorded using `compare_reviews`.
5. Resolution is documented.
6. If the underlying evidence or coding changes materially, a new audit receipt is issued with a new report hash.

## What does not qualify

- requests to improve a score without new evidence;
- payment-linked requests;
- requests to remove documented negative evidence without a factual basis;
- unsupported marketing claims;
- legal threats presented without evidence of a factual error.

Humanity Score is a due-diligence framework, not a court, regulator, or certification body.
