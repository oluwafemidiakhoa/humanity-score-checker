---
name: humanity-score-checker
display_name: Humanity Score Checker — Fair Trade Label for AI
version: 1.0.0
author: oluwafemidiakhoa
description: Scores any AI product on Agency, Value Capture, and Connection Depth. Returns Humanity Score 0-100 + Fair Trade badge. GateGuard verified with 2 sources + human story. Built from Humanity Score OS that scored 47 products.
price: 19
category: analytics & monitoring
tags: [humanity-score, fair-trade, ai-ethics, gateGuard, agency, viral-teardown]
mcp_market: true
license: MIT
repository: https://github.com/oluwafemidiakhoa/humanity-score-checker
---

# Humanity Score Checker — Fair Trade Label for AI

**The standard for AI that preserves human agency.** Scores any AI tool/product on human impact.

Built with **Humanity Score OS** — the OS that scraped mcpmarket.com (48,419 servers) and found the $19 x 388k = $7.4M pattern.

## What it does

This skill evaluates any AI product across 3 axes:

1. **Agency Preserved (0-100)**: Does it make humans MORE capable, not less? Does it preserve the user's ability to think, choose, witness?

2. **Value Capture (0-100)**: Who gets paid? Human creator or platform? $19 skill economy vs SaaS extraction.

3. **Connection Depth (0-100)**: Does it isolate humans or connect them? AI reveals loneliness vs creates it.

**Formula:** `Humanity Score = (Agency + Value + Connection) / 3`

- **80-100**: GREEN — HIGH HUMANITY — Fair Trade Badge
- **40-79**: YELLOW — MEDIUM — Needs improvement
- **0-39**: RED — LOW — Extractive

## Tools

### `score_product`

Scores an AI product.

**Input:**
- `product_name` (string): Name of product (e.g., "Meme Maker")
- `product_url` (string, optional): URL to product page, docs, or GitHub
- `description` (string): What it does
- `agency` (number 0-100): Your rating for Agency Preserved
- `value_capture` (number 0-100): Your rating for Value Capture
- `connection` (number 0-100): Your rating for Connection Depth
- `sources` (array of 2 strings): 2 primary sources (GateGuard requirement)
- `human_story` (string): 1 real human story of use (GateGuard requirement)

**Output:**
- `humanity_score` (number): 0-100
- `badge` (string): SVG badge code (GREEN/YELLOW/RED)
- `viral_thread` (array of 5 strings): Thiel-style teardown thread ready to post
- `gateGuard_passed` (boolean): True if 2 sources + 1 human story provided
- `tac_recommendation` (string): Time Aligned Capital / revenue insight

**Example:**

```json
{
  "product_name": "Meme Maker",
  "product_url": "https://app.mcpmarket.com/.../meme-maker",
  "description": "AI meme generator from text",
  "agency": 85,
  "value_capture": 80,
  "connection": 82,
  "sources": ["mcpmarket.com - 388k installs", "GitHub - 1.2k stars"],
  "human_story": "Writer shipped 3 essays/day using it to amplify witness, not replace thinking"
}
```

**Returns:**

```json
{
  "humanity_score": 82,
  "badge": "<svg>...82 - HIGH HUMANITY - Fair Trade</svg>",
  "viral_thread": ["1/ AI companions didn't make us lonely...", ...],
  "gateGuard_passed": true,
  "tac_recommendation": "$7.4M TAM — $19 pricing optimal — list on mcpmarket"
}
```

### `generate_badge`

Generates Fair Trade SVG badge for a score.

**Input:**
- `score` (number): 0-100
- `product_name` (string)

**Output:**
- `svg` (string): Badge SVG
- `markdown` (string): Markdown for product page

### `generate_viral_teardown`

Generates 5-tweet Thiel-style thread from a scored product.

**Input:**
- `product_name`, `score`, `thesis` ("reveals", "19skill", "witness")

**Output:**
- `thread` (array of 5 strings): Ready to post to X

## Why this skill sells

- **Pattern proven:** Top skills on mcpmarket.com = $19, 388k installs = $7.4M TAM. This skill rides that pattern but adds the missing layer: trust.
- **Viral built-in:** Every score generates a thread that tags founders → free distribution.
- **Contrarian thesis:** "AI Reveals Humans" — Thiel-level idea no one owns yet. This skill IS the standard.
- **GateGuard moat:** Requires 2 sources + human story — makes scores credible, not AI slop.

## Monetization play

1. List at $19 (same as top 5 skills)
2. Every score → post viral thread → tag founder → founder retweets → traffic to your mcpmarket storefront
3. Upsell: Full audit $500 for founders who want GREEN badge for their product page

From your Humanity Score OS thread: https://x.com/oluwafemiI53621/status/2104950092885278910

## Installation

1. Add to Claude / Cursor MCP config
2. Call `score_product` with any AI tool you find
3. Get score + badge + viral thread instantly

Built with 8 MCP skills: Deep Research, Exa Neural Search, Market Research, Data Scraper, Research Ops, GateGuard, Diagram Maker, Social Distributor.

---

**Fair Trade Label for AI. Score >70 gets badge.**
