# Humanity Score Audit — ModelBrew

**Status:** PRELIMINARY public audit  
**Audit date:** 2026-10-01  
**Humanity Score:** **62/100**  
**Band:** **YELLOW · EVIDENCE-BACKED**  
**Evidence confidence:** moderate  
**Rubric version:** 2.0.0  
**Report hash:** `40594ceef9a22a8879ff4e11237294891cc26db80d61e35d13a3439b6e6fb46e`

> This preliminary audit was prepared from publicly available ModelBrew primary-source documentation. ModelBrew has not yet been asked to verify the factual interpretation.

## Dimension scores

- Agency: **65/100**
- Value Distribution: **65/100**
- Human Connection: **55/100**

Unassessed criteria remain at the rubric's neutral baseline of 50. A neutral score is not a negative finding.

## Evidence used

### Agency / user_control
ModelBrew states that trained adapters can be downloaded and run on the user's own infrastructure rather than requiring continued hosted use.

Source: https://modelbrew.ai/faq

### Agency / reversibility
ModelBrew documents account deletion and data deletion controls, including a 14-day dataset retention window after a run completes.

Source: https://modelbrew.ai/terms

### Agency / transparency
ModelBrew documents source provenance, hash-chained audit history, and signed erasure certificates for its governed knowledge layer.

Source: https://modelbrew.ai/live-cl

### Value Distribution / data_rights
ModelBrew's terms state that users retain intellectual-property rights in uploaded datasets and that uploaded data is not used to train ModelBrew's own models.

Source: https://modelbrew.ai/terms

### Value Distribution / lock_in
ModelBrew says trained models and fact stores are exportable, with adapter weights and knowledge data portable outside the service.

Source: https://modelbrew.ai/faq

### Value Distribution / incentive_alignment
ModelBrew publishes per-token pricing, estimates costs before runs, and automatically refunds credits when a training job fails due to a system error.

Source: https://modelbrew.ai/pricing

### Human Connection / collaboration
ModelBrew documents multi-department and team workflows, role-based access, and audit logging intended for organizational use.

Source: https://modelbrew.ai/all-features

### Human Connection / accessibility
ModelBrew offers a free tier with no credit card required and provides both web and API paths for starting training.

Source: https://modelbrew.ai/pricing

## Evidence gaps

No direct public evidence was scored for:

- `agency.human_override`
- `value_distribution.user_benefit`
- `human_connection.substitution_risk`
- `human_connection.social_wellbeing`

These criteria remain at 50 rather than being inferred from adjacent claims.

## Correction path

ModelBrew may submit source-backed factual corrections or additional primary evidence. Corrections change the audit only when the underlying evidence changes; payment cannot buy a higher score.

## Limitations

- The score is only as strong as the evidence supplied to the audit.
- The audit validates evidence structure and provenance URLs but does not independently authenticate every source claim.
- Humanity Score is a product-impact rating, not a regulatory, legal, safety, compliance, or government certification.
