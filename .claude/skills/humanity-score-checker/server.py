"""Humanity Score Checker MCP server.

v2 separates self-reported scoring from evidence-backed auditing.
This entrypoint is configured for remote Streamable HTTP deployment.
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from core import audit_evidence, score_self_reported, share_thread, unverified_badge

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

mcp = FastMCP(
    "humanity-score-checker",
    host=HOST,
    port=PORT,
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def audit_product(
    product_name: str,
    description: str,
    evidence: list[dict[str, Any]],
    product_url: str = "",
    human_story: str = "",
) -> dict[str, Any]:
    """Run the recommended evidence-backed Humanity Score audit.

    Evidence items require:
    - dimension: agency | value_distribution | human_connection
    - criterion: one criterion from the published rubric
    - finding: factual finding (20+ characters)
    - source: http(s) provenance URL
    - source_type: primary | secondary | anecdotal
    - impact: -2 to +2
    - confidence: 0 to 1

    The tool computes criterion and dimension scores, evidence coverage,
    confidence, a deterministic report hash, and badge eligibility.
    """

    result = audit_evidence(
        product_name=product_name,
        description=description,
        evidence=evidence,
        product_url=product_url,
        human_story=human_story,
    )
    result["share_thread"] = share_thread(result)
    return result


@mcp.tool()
def score_product(
    product_name: str,
    description: str,
    agency: int,
    value_capture: int,
    connection: int,
    sources: list[str],
    human_story: str,
    product_url: str = "",
) -> dict[str, Any]:
    """Backward-compatible self-assessment from the v1 interface.

    This path is deliberately labeled self-reported. It never issues an
    evidence-backed badge. Use audit_product for a source-gated audit.
    """

    return score_self_reported(
        product_name=product_name,
        description=description,
        agency=agency,
        value_capture=value_capture,
        connection=connection,
        sources=sources,
        human_story=human_story,
        product_url=product_url,
    )


@mcp.tool()
def generate_badge(product_name: str, score: int) -> dict[str, Any]:
    """Generate an UNVERIFIED visual badge for a standalone score.

    Evidence-backed badges are issued only by audit_product after coverage
    gates pass.
    """

    return unverified_badge(product_name, score)


@mcp.tool()
def generate_viral_teardown(product_name: str, score: int) -> dict[str, Any]:
    """Generate conservative social copy for a standalone score.

    Because no evidence bundle is supplied, this output does not make source,
    TAM, or certification claims.
    """

    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        raise ValueError("score must be an integer from 0 to 100")
    return {
        "thread": [
            f"1/ I ran {product_name} through the Humanity Score framework: {score}/100.",
            "2/ The framework examines three questions: does the product preserve human agency, distribute value fairly, and strengthen human connection?",
            "3/ A number alone is not certification. Evidence coverage and provenance determine whether an audit is badge-eligible.",
            "4/ The evidence-backed audit publishes dimension scores, accepted findings, source coverage, limitations, and a reproducible report hash.",
            "5/ Humanity Score is a product-impact rating for AI. It is not a regulatory, legal, safety, or compliance certification.",
        ],
        "verification_status": "unverified",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
