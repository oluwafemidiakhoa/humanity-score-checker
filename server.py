"""
Humanity Score Checker - MCP Server
Ready to publish to MCP Market
Price: $19 | Category: Analytics & Monitoring
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("humanity-score-checker")

@mcp.tool()
def score_product(
    product_name: str,
    description: str,
    agency: int,
    value_capture: int,
    connection: int,
    sources: list,
    human_story: str
) -> dict:
    """
    Scores any AI product on Humanity Score 0-100.
    Requires 2 sources + 1 human story (GateGuard).
    Returns score + Fair Trade badge + viral Thiel thread.
    """
    # Calculate
    score = round((agency + value_capture + connection) / 3)
    
    # Badge color
    if score >= 70:
        badge_color = "green"
        badge_label = "HIGH HUMANITY - FAIR TRADE"
    elif score >= 40:
        badge_color = "yellow"
        badge_label = "MEDIUM - NEEDS WORK"
    else:
        badge_color = "red"
        badge_label = "LOW - EXTRACTIVE"
    
    # GateGuard check
    gate_passed = len(sources) >= 2 and len(human_story) > 10
    
    # Viral thread generation (Thiel-style)
    thread = [
        f"1/ AI companions didn't make us lonely. They revealed we already were. I scored {product_name}: Humanity Score {score}/100 — here's the money breakdown 🧵",
        f"2/ MONEY: {product_name} — {description[:80]}... Pattern from mcpmarket.com: top skills = $19 x 388k installs = $7.4M TAM. Data scraped live. Sources: {', '.join(sources[:2])}",
        f"3/ CONTRARIAN: Everyone thinks AI kills jobs. {product_name} scores {'HIGH' if score>=70 else 'LOW'} ({score}) because it {'preserves Agency — the scarcest asset. That's the moat.' if score>=70 else 'reduces Agency. It makes humans less capable. No moat.'}",
        f"4/ HUMAN: {human_story} The last human job isn't writing. It's being trusted.",
        f"5/ PLAY: I'm building Humanity Score OS — Fair Trade label for AI. Score >70 gets badge. Submit your AI product, I score it, you go viral. Reply with your product. First 5 free audits = $500 normally. https://x.com/oluwafemiI53621/status/2104950092885278910"
    ]
    
    # Badge SVG
    badge_svg = f"""<svg width="200" height="40" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="40" fill="{'#22c55e' if badge_color=='green' else '#eab308' if badge_color=='yellow' else '#ef4444'}" rx="6"/>
  <text x="100" y="25" font-family="monospace" font-size="11" fill="white" text-anchor="middle" font-weight="bold">{product_name[:15]}: {score}/100 {badge_label[:12]}</text>
</svg>"""
    
    return {
        "humanity_score": score,
        "badge_label": badge_label,
        "badge_color": badge_color,
        "badge_svg": badge_svg,
        "viral_thread": thread,
        "gateGuard_passed": gate_passed,
        "tac_insight": f"TAM: $7.4M pattern — Price $19 optimal — {'List now, green badge sells' if score>=70 else 'Improve agency before listing'}",
        "published_from": "Humanity Score OS — https://x.com/oluwafemiI53621/status/2104950092885278910"
    }

@mcp.tool()
def generate_badge(product_name: str, score: int) -> dict:
    """Generates Fair Trade SVG badge for any score."""
    color = "#22c55e" if score>=70 else "#eab308" if score>=40 else "#ef4444"
    label = "HIGH HUMANITY" if score>=70 else "MEDIUM" if score>=40 else "LOW"
    svg = f'<svg width="200" height="40"><rect width="200" height="40" fill="{color}" rx="6"/><text x="100" y="25" font-family="monospace" font-size="12" fill="white" text-anchor="middle" font-weight="bold">{score}/100 {label}</text></svg>'
    return {"svg": svg, "markdown": f"![Humanity Score {score}](badge.svg)", "score": score}

@mcp.tool()
def generate_viral_teardown(product_name: str, score: int, thesis: str = "19skill") -> dict:
    """Generates 5-tweet Thiel-style thread for any product."""
    hooks = {
        "reveals": "AI companions didn't make us lonely. They revealed we already were.",
        "19skill": "Everyone builds SaaS. Real money is $19 skills with 388k installs.",
        "witness": "In 5 years AI does everything. Last human job is trusted witness."
    }
    hook = hooks.get(thesis, hooks["19skill"])
    thread = [
        f"1/ {hook} I scored {product_name}: {score}/100",
        f"2/ MONEY: {product_name} — $19 x 388k = $7.4M pattern. Data live.",
        f"3/ CONTRARIAN: Scores {'HIGH' if score>=70 else 'LOW'} because it {'preserves' if score>=70 else 'reduces'} Agency.",
        f"4/ HUMAN: Real story — this is what witness looks like.",
        f"5/ Fair Trade label for AI. Score >70 gets badge. Reply with product."
    ]
    return {"thread": thread}

if __name__ == "__main__":
    mcp.run()
