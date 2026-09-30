FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/oluwafemidiakhoa/humanity-score-checker"
LABEL org.opencontainers.image.description="Humanity Score Checker MCP server"
LABEL org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY pyproject.toml README.md core.py server.py LICENSE ./

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "server.py"]
