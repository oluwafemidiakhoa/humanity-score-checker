# Humanity Score Checker — A Fair-Trade Label for AI

**Measure how well an AI product serves people—not just engagement, automation, or revenue.**

Humanity Score Checker evaluates an AI product on a **0–100 Humanity Score**, assigns a simple **GREEN / YELLOW / RED badge**, and generates a shareable five-post teardown explaining the result.

Built from **$7.4M TAM research**, including analysis of the MCP ecosystem, where the #1 Meme Maker has reached **388K installs on mcpmarket.com**.

**Live:** `app.mcpmarket.com/sellers/human-os`  
**Price:** $19

## How It Works

Provide:

- `product_name`
- `description`
- `agency`
- `value_capture`
- `connection`
- `sources`
- `human_story`

The checker evaluates three core dimensions:

**Agency** — Does the product increase human choice, control, and capability?

**Value Capture** — Does the product create meaningful value for people rather than simply extracting attention, data, or dependency?

**Human Connection** — Does the product strengthen human relationships, creativity, participation, or real-world connection?

It then returns:

- **Humanity Score:** 0–100
- **Badge:** GREEN, YELLOW, or RED
- **Viral Teardown:** five ready-to-share posts explaining the score

## Badge System

**GREEN — 70–100**  
Strong alignment with human agency, value creation, and connection.

**YELLOW — 40–69**  
Mixed performance. The product creates value but has meaningful areas for improvement.

**RED — 0–39**  
Weak alignment with the Humanity Score framework and significant room for redesign.

## MCP Tool

`score_product` — Python FastMCP server

```python
@mcp.tool()
def score_product(
    product_name: str,
    description: str,
    agency: int,
    value_capture: int,
    connection: int,
    sources: list,
    human_story: str
):
    score = round((agency + value_capture + connection) / 3)

    badge = (
        "green" if score >= 70
        else "yellow" if score >= 40
        else "red"
    )

    thread = [
        f"1/ AI didn't make us lonely. I scored {product_name}: {score}/100",
        f"2/ MONEY: {product_name} pattern — $19 × installs = TAM",
        f"3/ CONTRARIAN: {badge.upper()} — Agency is the moat",
        f"4/ HUMAN: {human_story}",
        f"5/ PLAY: Score above 70 earns the badge. First 3 free."
    ]

    return {
        "humanity_score": score,
        "badge": badge,
        "thread": thread
    }
```

## The Idea

AI products are usually measured by speed, accuracy, engagement, revenue, or automation.

Humanity Score asks a different question:

**Does this product leave the human being more capable, more connected, and more in control?**

Think of it as a **fair-trade label for AI**—a simple, public signal for products designed to create value without diminishing the people using them.

## License

MIT License

Copyright (c) 2026 Oluwafemi Idiakhoa

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files, subject to the terms of the MIT License.
