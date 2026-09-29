Humanity Score Checker — Publish TODAY Checklist
You are live. Stripe is active. 1 skill published, $0.00 until first sale. This is your system to go from $0 → $19.

LIVE ASSETS (from your screenshots)
GitHub: github.com/oluwafemidiakhoa/humanity-score-checker — LIVE with card
Storefront: mcpmarket.com/sellers/human-os — You're all set up — Published
X Thread: PLAY tweet 16 views (best) + Checker LIVE reply with GitHub card — 1m ago
Earnings: $0.00 / 0 Transactions → changes to $15.20 after first $19 sale (20% fee) — 14 day hold
How to Make Money While You Watch
You already did steps 1-5. Only Step 6 left: Drive clicks.

1. Storefront is LIVE
You have Human-OS workspace open. Don't create new listing. Your listing:

Name: humanity-score-checker
Display: Humanity Score Checker — Fair Trade Label for AI
Price: $19.00 Min $19
Tagline: Fair Trade label for AI — Scores any AI product 0-100 + badge + viral teardown
Status: Live
2. Code — Minimal server.py (use this, not advert code)

Your listing already points to GitHub. Ensure server.py in repo root:

Python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("humanity-score-checker")

@mcp.tool()
def score_product(product_name: str, description: str, agency: int, value_capture: int, connection: int, sources: list, human_story: str):
    score = round((agency + value_capture + connection)/3)
    badge = "green" if score>=70 else "yellow" if score>=40 else "red"
    thread = [
        f"1/ AI didn't make us lonely. It revealed we were. I scored {product_name}: {score}/100 🧵",
        f"2/ MONEY: {product_name} pattern live on mcpmarket.com — $19 x installs = TAM",
        f"3/ CONTRARIAN: Scores {score} — {badge.upper()} — Agency is moat",
        f"4/ HUMAN: {human_story}",
        f"5/ PLAY: Building Humanity Score OS — Fair Trade label. Score >70 gets badge. First 3 free."
    ]
    return {"humanity_score": score, "badge_color": badge, "viral_thread": thread, "gateGuard": len(sources)>=2}

if __name__ == "__main__":
    mcp.run()

13 lines hidden
Push to GitHub → MCP Market auto-syncs.

3. Stripe — DONE
You clicked Manage payouts on Stripe → Active → Now $19 sale = $15.20 settles automatically. You saw Sales settle to your Stripe balance on Earnings page.

4. Post — DONE, now PIN
Your X post from 1m ago:

Code
Checker LIVE: 【entity-github¦canonical_name=GitHub】.com/oluwafemidiakhoa/humanity-score-checker
First 3 free = $500 value. Reply with your product.
With GitHub card — Go pin your PLAY (16 views) tweet. That's your funnel top.

5. First Sale Loop (passive)

X card click → GitHub star → Click mcpmarket.com/sellers/human-os in README → Buy $19 → Your Earnings: TOTAL SALES $19.00 YOUR EARNINGS $15.20 TRANSACTIONS 1

No manual delivery. MCP Market handles checkout.
