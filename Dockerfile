FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/oluwafemidiakhoa/humanity-score-checker"
LABEL org.opencontainers.image.description="Humanity Score Checker MCP server"
LABEL org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY pyproject.toml requirements.lock README.md core.py server.py vercel_app.py audit_receipt.py intelligence.py governance.py provenance.py review.py LICENSE ./

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.lock \
    && python -m pip install --no-cache-dir --no-deps .

EXPOSE 8000

# MCPMarket managed deployments communicate over stdio.
# Direct HTTP hosts can override this command with:
#   python server.py --transport streamable-http
CMD ["python", "server.py", "--transport", "stdio"]
