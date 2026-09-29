# Humanity Score Checker

**Evidence-backed human-impact rating for AI products.**

Humanity Score Checker asks a simple question: **does an AI product leave people more capable, fairly served, and meaningfully connected?**

Version 2 separates two very different things:

- **Self-assessment** — a founder/user can enter three 0–100 ratings. This is useful for reflection, but it is always labeled `SELF-ASSESSED` and is **not badge eligible**.
- **Evidence-backed audit** — structured findings with source URLs are scored against a published rubric. Only audits that meet evidence coverage gates can receive an `EVIDENCE-BACKED` badge.

**MCPMarket launch price:** $19  
**Repository:** `github.com/oluwafemidiakhoa/humanity-score-checker`

> Humanity Score is a product-impact rating. It is not a regulatory, legal, safety, compliance, or third-party certification.

## Why v2 exists

The original prototype averaged three user-supplied numbers. That made it fast, but not independently meaningful. v2 keeps that interface for compatibility while moving the product toward a reproducible, source-gated audit.

There are no hard-coded TAM claims, no claim that data was scraped live, and no claim that a self-entered score is verified.

## Rubric

Each of 12 criteria starts at a neutral score of 50. Evidence shifts only the criterion it supports.

### Agency
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

Evidence uses:

- `impact`: `-2` to `+2`
- `confidence`: `0` to `1`
- `source_type`: `primary`, `secondary`, or `anecdotal`

Source type weights are 1.0, 0.75, and 0.50 respectively. Scores are clamped to 0–100.

## Badge thresholds

- **GREEN:** 70–100
- **YELLOW:** 40–69
- **RED:** 0–39

A color does **not** automatically mean the badge is evidence-backed.

To become badge eligible, an audit must contain at least:

- 6 accepted findings
- 3 unique source URLs
- evidence across all 3 dimensions
- 6 distinct rubric criteria
- 2 primary-source findings

Until those gates pass, the badge is marked **PROVISIONAL**.

## Recommended tool: `audit_product`

```json
{
  "product_name": "Example AI",
  "product_url": "https://example.com",
  "description": "AI assistant for collaborative research",
  "evidence": [
    {
      "dimension": "agency",
      "criterion": "user_control",
      "finding": "Users can disable automated actions and choose manual control at any time.",
      "source": "https://example.com/docs/control",
      "source_type": "primary",
      "impact": 2,
      "confidence": 1.0
    }
  ],
  "human_story": "Optional reported user context; it is not silently treated as verified evidence."
}
```

The result includes:

- Humanity Score 0–100
- criterion and dimension scores
- GREEN / YELLOW / RED band
- evidence coverage and confidence
- rejected-evidence reasons
- deterministic SHA-256 report hash
- evidence-backed or provisional badge
- factual five-post share thread
- limitations

## Backward-compatible tool: `score_product`

The original interface still works:

```text
product_name, description, agency, value_capture, connection, sources, human_story
```

But the output is explicitly:

```text
assessment_mode = self_reported
badge_eligible = false
```

This prevents a founder from entering `100, 100, 100` and presenting the result as an independently supported badge.

## Other tools

### `generate_badge`
Generates an **UNVERIFIED** visual badge for a standalone score. Evidence-backed badges are issued only from `audit_product`.

### `generate_viral_teardown`
Generates conservative share copy without inventing TAM, live-scraping, source, or certification claims.

## Running locally

```bash
python -m pip install "mcp>=1.0.0"
python server.py
```

## Testing

The scoring core uses only the Python standard library.

```bash
python -m unittest discover -s tests -v
python -m py_compile core.py server.py
```

## Methodology limitations

v2 validates evidence structure, URLs, source types, coverage, and deterministic scoring. It does **not** independently crawl the web or authenticate the contents behind a URL. An MCP host or researcher can gather the evidence first and pass it to `audit_product`.

A later version can add independent retrieval, source snapshots, signed audit receipts, appeals, and a public badge registry.

## License

MIT © 2026 Oluwafemi Idiakhoa
