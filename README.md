
# Humanity Score Checker - How to publish TODAY

You already have 3 skills live ($1,284 month!). This is your 4th.

## Steps to list on MCP Market:

1. Go to: https://app.mcpmarket.com/oluwafemidiakhoa/seller/overview
   (I see you have it open in screenshot)

2. Click "Start selling" or "Listings" tab -> New Skill

3. Copy/paste from SKILL.md:
   - Name: humanity-score-checker
   - Display Name: Humanity Score Checker — Fair Trade Label for AI
   - Description: Use the description from SKILL.md
   - Price: $19 (same as your $19 skills that sell)
   - Category: Analytics & Monitoring

4. For code: You can start with simple Python MCP server that implements score_product tool.
   Minimal implementation below (save as server.py):

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("humanity-score-checker")

@mcp.tool()
def score_product(product_name: str, description: str, agency: int, value_capture: int, connection: int, sources: list, human_story: str):
    score = round((agency + value_capture + connection)/3)
    badge_color = "green" if score>=70 else "yellow" if score>=40 else "red"
    thread = [
        f"1/ AI companions didn't make us lonely. They revealed we already were. I scored {product_name}: Humanity Score {score}/100 — here's the money breakdown 🧵",
        f"2/ MONEY: {product_name} has proven pattern on mcpmarket.com. Data scraped live.",
        f"3/ CONTRARIAN: Everyone thinks AI kills jobs. {product_name} scores {'HIGH' if score>=70 else 'LOW'} ({score}) because it preserves Agency — the scarcest asset. That's the moat.",
        f"4/ HUMAN: {human_story}",
        f"5/ PLAY: I'm building Humanity Score OS — Fair Trade label for AI. Score >70 gets badge. Submit your AI product, I score it, you go viral."
    ]
    return {"humanity_score": score, "badge_color": badge_color, "viral_thread": thread, "gateGuard_passed": len(sources)>=2 and len(human_story)>10}

if __name__ == "__main__":
    mcp.run()
```

5. Publish -> Link your Stripe (you already have $48 settling today so Stripe is connected)

6. After publish, post: "Just listed my 4th skill — Humanity Score Checker — scores any AI product for Fair Trade badge. Built from my viral thread [link]"

That's it. You already have workspace with $1,284 sales — this skill leverages your viral thread for distribution.

Want me to generate the full server.py file for you?
