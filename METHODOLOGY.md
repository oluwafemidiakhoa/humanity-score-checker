# Humanity Score Methodology

**Product version:** 3.3.1  
**Rubric version:** 3.2.1

Humanity Score is an evidence-backed AI product due-diligence framework. It evaluates documented evidence across Human Agency, Value Distribution, and Human Connection. It is not a regulatory, legal, safety, compliance, or government certification.

## Core principles

1. **Unknown is not neutral.** A criterion without accepted evidence is reported as `UNKNOWN`; it does not receive an implicit score of 50.
2. **Evidence is criterion-specific.** A finding moves only the criterion it supports.
3. **Independent source integrity is cryptographically gated.** A URL or caller-supplied hash is not verification. Badge eligibility requires valid Humanity Score Ed25519 snapshot attestations.
4. **Semantic support is separately reviewed.** A signed snapshot proves retrieval, not that a submitted finding is true. EVIDENCE-BACKED status requires a separate signed human claim-review attestation for every rubric criterion.
4. **Duplicate claims do not get extra weight.** Findings that represent the same underlying claim can share a `claim_id`; only the strongest-supported instance is counted.
5. **Contradictions are surfaced.** Positive and negative evidence for the same criterion is shown as unresolved contradiction rather than silently hidden.
6. **Human judgment is inspectable.** Impact and confidence are explicit fields with anchors and optional rationale/reviewer IDs.
7. **Payment cannot buy a result.** Commercial payment does not change evidence, scoring, badge eligibility, or conclusions.

## Rubric

### Human Agency
- `user_control`
- `reversibility`
- `transparency`
- `human_override`

### Value Distribution
- `user_benefit`
- `data_rights`
- `lock_in`
- `incentive_alignment`

### Human Connection
- `collaboration`
- `substitution_risk`
- `social_wellbeing`
- `accessibility`

## Evidence coding

Each accepted finding contains:

- dimension
- criterion
- finding
- source URL
- source type: `primary`, `secondary`, or `anecdotal`
- impact: one of `-2, -1, 0, +1, +2`
- confidence: `0.0–1.0`
- optional rationale
- optional reviewer ID
- optional claim ID for de-duplication
- optional source snapshot SHA-256
- optional source retrieval timestamp
- optional source content type and byte length
- optional Humanity Score snapshot signature and signing-key ID
- optional archive URL

### Impact anchors

| Impact | Interpretation |
|---:|---|
| -2 | Strong, directly supported evidence of material harm, loss of control, exclusion, or adverse incentive |
| -1 | Supported evidence of a meaningful concern or downside |
| 0 | Supported evidence is mixed, neutral, or not directionally informative |
| +1 | Supported evidence of a meaningful benefit, control, safeguard, or positive outcome |
| +2 | Strong, directly supported evidence of a material benefit, safeguard, or positive outcome |

### Confidence anchors

- **Low:** material ambiguity, indirect evidence, or unresolved interpretation.
- **Moderate:** evidence substantially supports the finding but leaves meaningful uncertainty.
- **High:** direct, specific evidence with little interpretive uncertainty.

The machine field remains numeric because scoring is deterministic; reviewers should document rationale when the coding is not obvious.

## Scoring

For a covered criterion, scoring begins at 50 and evidence shifts it:

`criterion_score = 50 + Σ(impact × 12.5 × confidence × source_weight)`

Source weights:

- primary = 1.00
- secondary = 0.75
- anecdotal = 0.50

The score is clamped to 0–100.

A criterion with no accepted evidence is **UNKNOWN**, not 50.

Dimension scores are calculated only from criteria that have accepted evidence.

An overall Humanity Score is withheld until evidence covers:

- all three dimensions, and
- at least six distinct criteria.

This prevents missing evidence from appearing as neutral evidence.

## Badge eligibility

An audit can be labeled `EVIDENCE-BACKED` only when all of the following are true:

- an overall score exists;
- at least 6 accepted findings;
- at least 3 distinct source sites;
- all 3 dimensions covered;
- at least 6 distinct criteria covered;
- at least 2 primary-source findings;
- at least 2 distinct source sites with valid Humanity Score Ed25519 snapshot attestations.

Otherwise the audit is `PROVISIONAL` or `UNSCORED`.

## Source snapshots and proof of time

The `snapshot_source` tool retrieves a public URL using a bounded, private-network-blocking, DNS-pinned fetcher and returns:

- requested and final URL
- retrieval timestamp
- SHA-256 of the retrieved bytes
- content type and byte length
- bounded text excerpt
- a Humanity Score Ed25519 attestation when production signing is configured

The hash identifies the retrieved bytes. The source signature prevents a caller from inventing a hash/timestamp pair and presenting it as Humanity Score-retrieved evidence. This still does not establish that a reviewer-authored finding is semantically supported by those bytes. That second step is represented by a separate human claim-review attestation signed with an offline reviewer key. It does **not**, by itself, prove when those bytes first existed. For independent proof of time, persist the snapshot or hash in a trusted external timestamp/archive service.

## Duplicate and derived evidence

Two findings can share the same `claim_id` when they restate or derive from one underlying claim. Humanity Score counts only the strongest-supported instance for scoring and records the dropped duplicate.

If no claim ID is supplied, an exact normalized finding fingerprint is used. Semantic duplicates with different wording still require reviewer judgment to assign a common claim ID.

## Contradictions

If accepted findings on the same criterion include both positive and negative impacts, the audit records an unresolved contradiction. Contradictions reduce confidence in high-confidence cases and should be addressed in reviewer notes or follow-up evidence.

## Independent review and calibration

The `compare_reviews` tool compares two independent reviewer coding passes by criterion and claim ID. It reports:

- overlap
- exact agreement rate
- coverage disagreements
- impact disagreements
- confidence disagreements

Disagreements are not silently averaged. They require documented adjudication.

## Corrections and appeals

The `create_appeal` tool creates a deterministic correction/appeal record tied to a report hash. A correction must be evidence-backed. Payment, customer status, or reputational pressure does not determine resolution.

## Legacy public cohort

The public audits dated 2026-10-01 through 2026-10-02 were produced with rubric 2.0.0 and are preserved as historical receipts. They should not be silently relabeled as rubric 3.0.0. A future re-audit must create a new report hash and new receipt.


## Production trust boundary

`source_type` and `confidence` are required. Missing values are rejected rather than receiving optimistic defaults.

A source is marked `source_verified=true` only when all signed snapshot fields validate against the deployment's configured Ed25519 public key. Caller-supplied SHA-256 values, timestamps, content types, byte counts, or signatures that do not verify remain unverified.

Public audit receipts carry a server-generated `issued_at` timestamp. When production signing is configured, `create_audit_receipt` returns an Ed25519 signature over the complete receipt. The signature attests issuance by that configured Humanity Score key; it is not an external trusted timestamp.

Direct HTTP deployments must be authenticated and rate-limited. The provided Vercel entry point is fail-closed until `HUMANITY_SCORE_API_KEY` is configured.


## Claim-review authority

The production source-snapshot/receipt signing key and the human-review signing key are intentionally different trust domains.

- `HUMANITY_SCORE_SIGNING_KEY`: service key used for source snapshots and receipt issuance.
- `HUMANITY_SCORE_REVIEW_SIGNING_KEY`: privileged offline key used only by a human reviewer after inspecting findings against captured sources.
- `HUMANITY_SCORE_TRUSTED_PUBLIC_KEYS_JSON`: historical service public keys retained for verification after rotation.
- `HUMANITY_SCORE_TRUSTED_REVIEW_PUBLIC_KEYS_JSON`: trusted reviewer public keys, including historical ones.

The public MCP should not receive the reviewer private key. It should only know the public keys needed to verify reviewer attestations.

A signed human claim-review attestation binds the dimension, criterion, finding text, source URL, source type, impact, confidence, claim ID, source snapshot identity, reviewer ID, and review timestamp. Changing any of those fields invalidates the attestation.

## Receipt verification

`verify_receipt` checks the receipt signature against the current service public key or an explicitly trusted historical service key. A valid signature proves that the configured Humanity Score signing authority signed that exact receipt. It does not certify the audited product or independently prove the truth of every underlying claim.
