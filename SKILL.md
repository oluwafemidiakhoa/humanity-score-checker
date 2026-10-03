---
name: humanity-score-checker
display_name: Humanity Score Checker — Evidence-Backed Human Impact Rating for AI
version: 3.1.1
author: oluwafemidiakhoa
description: Independent AI product due diligence across Agency, Value Distribution, and Human Connection, with explicit unknowns, source snapshots, duplicate/contradiction checks, reviewer calibration, and reproducible receipts.
price: 19
category: "analytics & monitoring"
tags: [humanity-score, ai-ethics, product-audit, agency, evidence, transparency]
mcp_market: true
license: MIT
repository: https://github.com/oluwafemidiakhoa/humanity-score-checker
---

# Humanity Score Checker

**Evidence-backed human-impact rating for AI products.**

The skill evaluates whether an AI product preserves human agency, distributes value fairly, and strengthens human connection.

## Recommended tool: `audit_product`

Use this for a source-gated audit.

### Inputs

- `product_name` (string)
- `description` (string)
- `product_url` (string, optional)
- `human_story` (string, optional)
- `evidence` (array of objects), each containing:
  - `dimension`: `agency`, `value_distribution`, or `human_connection`
  - `criterion`: a criterion from the published rubric
  - `finding`: factual finding, at least 20 characters
  - `source`: HTTP(S) source URL
  - `source_type`: `primary`, `secondary`, or `anecdotal`
  - `impact`: -2 to +2
  - `confidence`: 0 to 1

### Outputs

- `humanity_score`
- `dimension_scores`
- `criterion_scores`
- `badge_color`
- `badge_label`
- `badge_eligible`
- `evidence_confidence`
- `evidence_summary`
- `rejected_evidence`
- `report_hash`
- `badge_svg`
- `share_thread`
- `unknown_criteria`
- `source_integrity`
- `contradictions`
- `duplicate_evidence`
- `limitations`

### Evidence-backed badge gate

An audit is badge eligible only when it has at least:

- 6 accepted findings
- 3 unique source URLs
- coverage across all 3 dimensions
- 6 distinct rubric criteria
- 2 primary-source findings
- 2 unique source URLs with independently retrieved snapshot hashes and retrieval timestamps

Badge colors:

- GREEN: 70–100
- YELLOW: 40–69
- RED: 0–39

A color band is not itself verification. If minimum coverage is not met, the audit is `UNSCORED`; if a score exists but the stricter badge gate is not met, it is `PROVISIONAL`.

## `score_product`

Backward-compatible v1 self-assessment. The caller supplies Agency, Value Capture, and Connection scores.

The result is always labeled:

- `assessment_mode: self_reported`
- `badge_eligible: false`

Self-reported scores cannot receive an evidence-backed badge.

## `generate_badge`

Creates an unverified visual badge for a standalone score. Only `audit_product` can return an evidence-backed badge.

## `generate_viral_teardown`

Creates a conservative five-post share thread without unsupported claims about TAM, live scraping, evidence, or certification.

## Rubric

### Agency
`user_control`, `reversibility`, `transparency`, `human_override`

### Value Distribution
`user_benefit`, `data_rights`, `lock_in`, `incentive_alignment`

### Human Connection
`collaboration`, `substitution_risk`, `social_wellbeing`, `accessibility`

A covered criterion starts at 50 and evidence shifts only that criterion. An uncovered criterion is UNKNOWN and is not silently treated as neutral. Source type and confidence weight the impact. An overall score is withheld until all 3 dimensions and at least 6 criteria are covered. The full methodology is documented in METHODOLOGY.md.

## Additional tools

- `version_info`: verifies the deployed release and expected tool count.
- `snapshot_source`: safely retrieves a public source and returns SHA-256 + retrieval metadata.
- `decision_brief`: turns an audit into prioritized buyer/founder actions and questions.
- `monitor_product_change`: compares evidence snapshots over time.
- `create_audit_receipt`: creates a deterministic public receipt.
- `compare_reviews`: compares independent reviewer coding passes.
- `create_appeal`: creates a deterministic correction/appeal intake record.
- `procurement_packet`: packages an audit for procurement/governance intake.
- `evidence_requests`: generates targeted vendor evidence requests for missing or weak criteria.

## Important limitation

A source snapshot hash proves the bytes retrieved by Humanity Score, but without an external trusted timestamp/archive it does not independently prove when those bytes first existed. Humanity Score is a product-impact and due-diligence framework, not regulatory, legal, safety, compliance, or third-party certification.

## Release verification

For MCPMarket or any managed host, call `version_info`. Humanity Score 3.1.1 should report `tool_count_expected: 13`. If a host still exposes only the original four tools, it is serving a stale deployment and should be replaced with a fresh deployment from the current GitHub `main` branch.
