# Humanity Score Checker

**Independent, evidence-backed AI product due diligence.**

Humanity Score asks: **before a buyer, founder, procurement team, or investor trusts an AI product, what does the documented evidence actually support about Human Agency, Value Distribution, and Human Connection?**

**Product version:** 3.3.0  
**Current rubric:** 3.2.0  
**Founder Audit:** $499 one-time — [Book the audit](https://book.stripe.com/eVq3cu0N71pucyIf8Eao80b)  
**MCPMarket tool price:** $19

> Humanity Score is a product-impact and due-diligence framework. It is not legal advice, regulatory approval, safety certification, compliance certification, or government certification.

## What changed in 3.3

Rubric 3.2 closes the semantic trust gap left after snapshot signing:

- **A signed snapshot is not enough.** EVIDENCE-BACKED status now requires a signed Humanity Score human claim-review attestation showing that each scored finding was reviewed against its captured source.
- **Full-rubric badge coverage is required.** EVIDENCE-BACKED status requires all 12 criteria, at least 12 accepted findings, at least 6 distinct source sites, at least 3 primary findings, and at least 3 independently snapshotted source sites.
- **Human-review authority is separated from the public service key.** Claim-review signatures use a separate offline `HUMANITY_SCORE_REVIEW_SIGNING_KEY`; the public MCP should receive only trusted review public keys.
- **Historical signing keys can remain trusted after key rotation.**
- **Non-global IPs are blocked.** Source retrieval now requires globally routable IP addresses.
- **Public receipt verification is first-class.** `verify_receipt` verifies receipt signatures.
- **Raw `server.py --transport streamable-http` is disabled by default.** Authenticated HTTP should use `vercel_app.py`; insecure raw HTTP requires an explicit local-test override.
- **Production container publishing is CI-gated.** Images publish only after successful main-branch CI.

The previous 3.2 protections remain:

- **Caller-supplied hashes no longer count as verified evidence.** Badge verification requires a valid Humanity Score Ed25519 snapshot attestation.
- **Source snapshots are DNS-pinned.** The fetcher resolves and validates a public IP, then connects to that exact IP; redirects are revalidated.
- **Strong defaults were removed.** `source_type` and `confidence` are required rather than defaulting to primary/1.0.
- **Source-site inflation is reduced.** Multiple subdomains of the same site do not count as independent badge sources.
- **Receipts and appeals are signed when a signing key is configured.** Public receipts include a server issuance timestamp.
- **Direct Vercel MCP is fail-closed.** Set `HUMANITY_SCORE_API_KEY` before exposing `/mcp`; per-minute rate limiting is included.
- **Runtime dependencies are pinned.** CI and managed-host builds use exact tested versions.
- **Public receipt consistency is tested in CI.** Markdown metadata must match canonical JSON.

The previous rubric-3 protections remain:

- **Unknown is not neutral.** Criteria without accepted evidence are reported as `UNKNOWN`; they are not silently scored 50.
- **Overall scores can be withheld.** An audit stays `UNSCORED` until evidence covers all 3 dimensions and at least 6 distinct criteria.
- **Source integrity is explicit.** Evidence can include independently retrieved snapshot SHA-256 hashes and retrieval timestamps.
- **Badge eligibility is source-gated.** Source snapshots must carry valid Humanity Score signatures.
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

Snapshot metadata is optional for accepting a finding. For an `EVIDENCE-BACKED` badge, however, snapshot metadata only counts when it carries a valid Humanity Score Ed25519 attestation produced by `snapshot_source`.

## Badge and scoring gates

An overall score is produced only after evidence covers:

- all 3 dimensions; and
- at least 6 distinct criteria.

Badge eligibility additionally requires:

- at least 12 accepted findings;
- all 12 rubric criteria covered;
- all 3 dimensions covered;
- at least 6 distinct source sites;
- at least 3 primary-source findings;
- at least 3 distinct source sites with valid Humanity Score signed snapshot attestations;
- a valid signed Humanity Score human claim-review attestation for every criterion;
- no unresolved contradictions.

Until those gates pass, the audit is `PROVISIONAL` or `UNSCORED`.

Color bands apply only when an overall score exists:

- GREEN: 70–100
- YELLOW: 40–69
- RED: 0–39

A color band is not certification.

## MCP tools

### `version_info`
Returns the deployed product version, rubric version, and expected tool count. Use it to verify that a managed host is not serving a stale build.

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
- signed snapshot attestation fields that can be copied directly into an evidence item

The fetcher rejects localhost/private/reserved network destinations, pins the validated public IP for the connection, revalidates redirects, and enforces redirect/response-size limits.

A valid Humanity Score attestation proves that the configured Humanity Score deployment retrieved the represented bytes and metadata. It does **not** independently prove when those bytes first existed; use a trusted external timestamp or archival service when independent proof of time is required.

### `verify_receipt`
Verifies that an audit receipt was signed by the current Humanity Score service key or a trusted historical signing key. Signature validity attests issuance of that exact receipt; it is not product certification.

### `decision_brief`
Adds prioritized actions, buyer questions, review signals, monitoring triggers, unknown criteria, contradictions, and source-integrity context.

### `monitor_product_change`
Compares two evidence snapshots and reports score/coverage/evidence changes.

### `create_audit_receipt`
Produces a shareable receipt with source-integrity metadata, a server issuance timestamp, and an Ed25519 signature when signing is configured.

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
python -m pip install -r requirements.lock
python -m pip install --no-deps .
python server.py
```

For local HTTP smoke testing only:

```bash
HUMANITY_SCORE_ALLOW_INSECURE_HTTP=1 python server.py --transport streamable-http
```

Do not use that raw HTTP mode for public production traffic.

## Testing

```bash
python -m unittest discover -s tests -v
python -m py_compile core.py server.py vercel_app.py audit_receipt.py intelligence.py governance.py provenance.py review.py review_cli.py
```

## Security boundary

`snapshot_source` is designed only for public web evidence. It rejects local/private/reserved network destinations, limits redirects, uses a response-size cap, and does not accept embedded URL credentials.

## License

MIT © 2026 Oluwafemi Idiakhoa


## Production configuration

For source snapshots and audit receipts, configure a stable 32-byte Ed25519 private key in `HUMANITY_SCORE_SIGNING_KEY` (64 hex characters or base64url). Keep this service key secret and stable across deployments.

Human claim review uses a **separate offline authority**. Keep `HUMANITY_SCORE_REVIEW_SIGNING_KEY` off the public MCP server. A human reviewer uses it only with the repository's privileged `review_cli.py` after manually checking each finding against its captured source. Public deployments should receive the corresponding trusted review public key via `HUMANITY_SCORE_TRUSTED_REVIEW_PUBLIC_KEYS_JSON`.

Historical service public keys may be retained through `HUMANITY_SCORE_TRUSTED_PUBLIC_KEYS_JSON`; historical review public keys may be retained through `HUMANITY_SCORE_TRUSTED_REVIEW_PUBLIC_KEYS_JSON`.

For the direct Vercel HTTP MCP endpoint, also configure `HUMANITY_SCORE_API_KEY`. Requests to `/mcp` fail closed when this variable is absent. The in-process rate limiter is only a local safeguard; use platform-level/global rate limiting for a public high-volume endpoint.

MCPMarket's managed stdio deployment does not require the HTTP API key. It does need `HUMANITY_SCORE_SIGNING_KEY` for signed source snapshots and the trusted review public-key registry to recognize independently reviewed claims.
