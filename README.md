# Humanity Score Checker

**Independent, evidence-backed AI product due diligence.**

Humanity Score asks: **before a buyer, founder, procurement team, or investor trusts an AI product, what does the documented evidence actually support about Human Agency, Value Distribution, and Human Connection?**

**Product version:** 3.1.0  
**Current rubric:** 3.0.0  
**Founder Audit:** $499 one-time — [Book the audit](https://book.stripe.com/eVq3cu0N71pucyIf8Eao80b)  
**MCPMarket tool price:** $19

> Humanity Score is a product-impact and due-diligence framework. It is not legal advice, regulatory approval, safety certification, compliance certification, or government certification.

## What changed in 3.1

Rubric 3.0 hardens the evidence model:

- **Unknown is not neutral.** Criteria without accepted evidence are reported as `UNKNOWN`; they are not silently scored 50.
- **Overall scores can be withheld.** An audit stays `UNSCORED` until evidence covers all 3 dimensions and at least 6 distinct criteria.
- **Source integrity is explicit.** Evidence can include independently retrieved snapshot SHA-256 hashes and retrieval timestamps.
- **Badge eligibility is stricter.** At least 2 unique sources must be independently snapshotted.
- **Duplicate/derived claims are de-duplicated.** A shared `claim_id` prevents repeated versions of one claim from accumulating extra weight.
- **Contradictions are visible.** Positive and negative evidence on the same criterion is surfaced instead of hidden.
- **Reviewer calibration is supported.** Independent coding passes can be compared and disagreements inspected.
- **Corrections/appeals are auditable.** Appeal records tie challenges to immutable report hashes.

See [METHODOLOGY.md](./METHODOLOGY.md) for the full methodology.

## Positioning

Humanity Score is **not** trying to replace enterprise AI-governance suites.

It is designed as an independent evidence layer for questions such as:

- What can be verified about this AI product before we buy or deploy it?
- Which human-impact claims are supported by evidence?
- Where are the evidence gaps?
- Which due-diligence questions should a buyer ask next?
- What changed since the last audit?

The intended workflow is:

`AI product → evidence → Humanity Score audit → decision brief → verification receipt → procurement / governance workflow`

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

For a covered criterion:

`criterion_score = 50 + Σ(impact × 12.5 × confidence × source_weight)`

Source weights:

- primary = 1.00
- secondary = 0.75
- anecdotal = 0.50

A criterion with no accepted evidence is **UNKNOWN**, not 50.

## Evidence format

A finding can include:

```json
{
  "dimension": "agency",
  "criterion": "user_control",
  "finding": "Users can disable automated actions and choose manual control at any time.",
  "source": "https://example.com/docs/control",
  "source_type": "primary",
  "impact": 2,
  "confidence": 1.0,
  "rationale": "Direct product documentation for the control.",
  "reviewer_id": "reviewer-a",
  "claim_id": "user-control-disable-actions",
  "source_snapshot_sha256": "64-hex-character-sha256",
  "source_retrieved_at": "2026-10-03T20:00:00Z",
  "source_archive_url": "https://archive.example/snapshot"
}
```

The snapshot fields are optional for accepting a finding, but are required in aggregate for an `EVIDENCE-BACKED` badge under rubric 3.0.

## Badge and scoring gates

An overall score is produced only after evidence covers:

- all 3 dimensions; and
- at least 6 distinct criteria.

Badge eligibility additionally requires:

- at least 6 accepted findings;
- at least 3 unique source URLs;
- at least 2 primary-source findings;
- at least 2 unique source URLs with snapshot hash + retrieval timestamp.

Until those gates pass, the audit is `PROVISIONAL` or `UNSCORED`.

Color bands apply only when an overall score exists:

- GREEN: 70–100
- YELLOW: 40–69
- RED: 0–39

A color band is not certification.

## MCP tools

### `audit_product`
Runs the evidence-backed audit.

Returns:

- Humanity Score or `UNSCORED`
- criterion and dimension scores
- explicit unknown criteria
- evidence coverage
- duplicate evidence records
- contradictions
- source integrity metadata
- evidence confidence
- rejected evidence reasons
- deterministic SHA-256 report hash
- evidence-backed/provisional status
- conservative share thread
- limitations

### `snapshot_source`
Safely retrieves a **public** evidence URL and returns:

- requested/final URL
- retrieval timestamp
- SHA-256 of retrieved bytes
- content type
- byte length
- bounded text excerpt

The fetcher rejects localhost/private/reserved network destinations and enforces redirect and response-size limits.

A snapshot hash proves what bytes were retrieved by the tool. It does **not** independently prove when those bytes first existed; use a trusted timestamp or archival service when independent proof of time is required.

### `decision_brief`
Adds prioritized actions, buyer questions, review signals, monitoring triggers, unknown criteria, contradictions, and source-integrity context.

### `monitor_product_change`
Compares two evidence snapshots and reports score/coverage/evidence changes.

### `create_audit_receipt`
Produces a shareable deterministic receipt with source-integrity metadata.

### `compare_reviews`
Compares two independent reviewer coding passes. It reports coverage disagreements, impact differences, confidence differences, and an exact agreement rate. Disagreements are not silently averaged.

### `create_appeal`
Creates a deterministic correction/appeal intake record tied to a report hash.

### `procurement_packet`
Runs an audit and packages the result for procurement/governance intake, including explicit unknowns, source integrity, contradictions, monitoring triggers, and targeted evidence requests.

### `evidence_requests`
Returns a vendor evidence-request checklist for missing or weak criteria. Framework mappings are non-certifying and are intended to support, not replace, formal legal/security/privacy/compliance processes.

### `score_product`
Backward-compatible self-assessment. It is always:

```text
assessment_mode = self_reported
badge_eligible = false
```

### `generate_badge`
Creates an **UNVERIFIED** visual badge for a standalone score.

### `generate_viral_teardown`
Creates conservative share copy without unsupported claims.

## Founder Audit

The $499 Founder Audit is for **one AI product** and includes:

- evidence-backed Humanity Score assessment
- Agency, Value Distribution, and Human Connection review
- criterion-level findings
- explicit unknowns, evidence gaps, contradictions, and limitations
- prioritized action brief
- buyer due-diligence questions
- shareable verification receipt
- reproducible report hash

Payment cannot buy a higher score, favorable badge, or favorable conclusion.

See [FOUNDER_AUDIT.md](./FOUNDER_AUDIT.md).

## Public proof

The [Humanity Score Index](./public_audits/README.md) contains 12 preliminary public audits.

Important version note: the public cohort dated 2026-10-01 through 2026-10-02 was produced using **rubric 2.0.0**. Those historical receipts remain immutable. They are not silently relabeled as rubric 3.0.0. A future re-audit must create a new receipt and report hash.

## Governance interoperability

[The governance crosswalk](./GOVERNANCE_CROSSWALK.md) maps Humanity Score evidence to common governance themes for procurement and risk discussions.

It is explicitly **non-certifying**. It does not establish conformity with NIST AI RMF, ISO/IEC 42001, the EU AI Act, or any other framework.

## Corrections and appeals

See [CORRECTIONS.md](./CORRECTIONS.md).

Historical receipts are immutable. Evidence-backed corrections produce a new audit/result rather than rewriting prior evidence history.

## Running locally

```bash
python -m pip install "mcp>=1.13,<2"
python server.py
```

## Testing

```bash
python -m unittest discover -s tests -v
python -m py_compile core.py server.py audit_receipt.py intelligence.py provenance.py review.py
```

## Security boundary

`snapshot_source` is designed only for public web evidence. It rejects local/private/reserved network destinations, limits redirects, uses a response-size cap, and does not accept embedded URL credentials.

## License

MIT © 2026 Oluwafemi Idiakhoa
