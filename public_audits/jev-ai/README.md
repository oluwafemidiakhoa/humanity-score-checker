# Humanity Score Audit — Jev AI

**Status:** PRELIMINARY public audit  
**Audit date:** 2026-10-01  
**Humanity Score:** **63/100**  
**Band:** **YELLOW · EVIDENCE-BACKED**  
**Evidence confidence:** moderate  
**Rubric version:** 2.0.0  
**Report hash:** `9ca62381c3ed5f1ef90e0e372f6979b9d4b6d70b34b61694e741ee8964c5575a`

> This preliminary audit was prepared from publicly available Jev AI primary-source documentation. Jev AI has not yet been asked to verify the factual interpretation.

## Dimension scores

- Agency: **68/100**
- Value Distribution: **58/100**
- Human Connection: **62/100**

Unassessed criteria remain at the rubric's neutral baseline of 50. A neutral score is not a negative finding.

## Evidence used

### Agency / user_control
Jev AI documents that application code keeps control of business logic, thresholds, permissions, and final actions while Jev supplies a typed decision signal.

Source: https://thejevai.com/about

### Agency / transparency
Jev exposes typed answer shapes, probabilities and confidence signals, and its developer documentation recommends logging question IDs, model versions, selected answers, probabilities, and downstream actions.

Source: https://thejevai.com/docs

### Agency / human_override
Jev's guidance explicitly calls for human-review routes for uncertain, novel, or high-impact decisions and says critical actions should retain deterministic or human fallback.

Source: https://thejevai.com/blog/jev-ai-agent-guardrails

### Value Distribution / user_benefit
Jev publishes a free unlimited online playground and low-entry paid tiers intended to let teams validate a workflow before production adoption.

Source: https://thejevai.com/

### Value Distribution / incentive_alignment
Jev publishes one-time credit pricing that does not auto-renew and lists the included credits, workspaces, concurrency, support, and collaboration features for each tier.

Source: https://thejevai.com/pricing

### Value Distribution / lock_in
Jev is exposed through a documented REST endpoint and agent skill while the surrounding application retains its own state, policies, thresholds, and actions, reducing dependency on a Jev-owned workflow surface.

Source: https://github.com/jev-ai/jev-api

### Human Connection / collaboration
Jev's Enterprise tier includes team workspaces and collaboration alongside custom integration support and dedicated support for shared organizational use.

Source: https://thejevai.com/pricing

### Human Connection / substitution_risk
Jev repeatedly positions the model as a decision signal inside human-governed workflows rather than a replacement for application logic, and recommends human review for uncertain or high-impact actions.

Source: https://thejevai.com/about

### Human Connection / accessibility
Jev provides a free online playground with unlimited runs and public documentation so users can test the decision workflow before buying API access.

Source: https://thejevai.com/

## Evidence gaps

No direct public evidence was scored for:

- `agency.reversibility`
- `value_distribution.data_rights`
- `human_connection.social_wellbeing`

Those criteria remain at 50 rather than being inferred from adjacent claims.

## Correction path

Jev AI may submit source-backed factual corrections or additional primary evidence. Corrections change the audit only when the underlying evidence changes; payment cannot buy a higher score.

## Limitations

- This preliminary audit uses public Jev AI primary-source documentation and has not been reviewed by Jev AI.
- Published product documentation is evidence of documented controls and policies, not proof of real-world outcomes for every deployment.
- Humanity Score is a product-impact rating, not a regulatory, legal, safety, compliance, or government certification.
