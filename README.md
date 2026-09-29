# Humanity Score Checker — Fair Trade Label for AI

Scores any AI product 0-100 + badge + viral teardown.

Built from $7.4M TAM research: Meme Maker #1 has 388k installs on mcpmarket.com.

**Live:** app.mcpmarket.com/sellers/human-os — $19

### How it works
- Input: product_name, description, agency, value_capture, connection, sources, human_story
- Output: humanity_score (0-100), badge (green/yellow/red), viral thread (5 tweets)

Badge: GREEN if >=70, YELLOW if >=40, RED if <40

### Tool
`score_product` — Python FastMCP server

```python
@mcp.tool()
def score_product(product_name: str, description: str, agency: int, value_capture: int, connection: int, sources: list, human_story: str):
    score = round((agency + value_capture + connection)/3)
    badge = "green" if score>=70 else "yellow" if score>=40 else "red"
    thread = [f"1/ AI didn't make us lonely. I scored {product_name}: {score}/100", f"2/ MONEY: {product_name} pattern — $19 x installs = TAM", f"3/ CONTRARIAN: {badge.upper()} — Agency is moat", f"4/ HUMAN: {human_story}", f"5/ PLAY: Score >70 gets badge. First 3 free."]
    return {"humanity_score": score, "badge": badge, "thread": thread}
