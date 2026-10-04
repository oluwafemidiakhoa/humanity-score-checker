"""Humanity Score Checker MCP server.

Defaults to stdio for managed MCP hosts. Streamable HTTP remains available
for direct hosting via --transport streamable-http or MCP_TRANSPORT.
"""

from __future__ import annotations

import argparse
import os
import time
from collections import deque
from typing import Any

from mcp.server.fastmcp import FastMCP

from audit_receipt import build_public_receipt, receipt_html, receipt_markdown
from core import PRODUCT_VERSION, RUBRIC_VERSION, audit_evidence, score_self_reported, share_thread, unverified_badge
from intelligence import build_decision_intelligence, compare_audit_results
from governance import build_procurement_packet, evidence_request_checklist
from provenance import retrieve_source_snapshot, review_signing_metadata, sign_document, signing_metadata, verify_document_signature
from review import compare_reviewer_evidence, create_appeal_record

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

_SNAPSHOT_CALLS: deque[float] = deque()


def _enforce_snapshot_rate_limit() -> None:
    try:
        limit = int(os.getenv("HUMANITY_SCORE_SNAPSHOT_RATE_LIMIT_PER_MINUTE", "30"))
    except ValueError:
        limit = 30
    limit = max(1, min(limit, 300))
    now = time.monotonic()
    while _SNAPSHOT_CALLS and now - _SNAPSHOT_CALLS[0] >= 60:
        _SNAPSHOT_CALLS.popleft()
    if len(_SNAPSHOT_CALLS) >= limit:
        raise ValueError("snapshot_source rate limit exceeded; retry later")
    _SNAPSHOT_CALLS.append(now)


mcp = FastMCP(
    "humanity-score-checker",
    host=HOST,
    port=PORT,
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def version_info() -> dict[str, Any]:
    """Return deployment/version information for cache and release verification."""
    return {
        "service": "humanity-score-checker",
        "product_version": PRODUCT_VERSION,
        "rubric_version": RUBRIC_VERSION,
        "tool_count_expected": 14,
        "provenance_signing": signing_metadata(),
        "claim_review_signing": review_signing_metadata(),
    }


@mcp.tool()
def audit_product(
    product_name: str,
    description: str,
    evidence: list[dict[str, Any]],
    product_url: str = "",
    human_story: str = "",
) -> dict[str, Any]:
    """Run the recommended evidence-backed Humanity Score audit."""
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
def create_audit_receipt(
    product_name: str,
    description: str,
    evidence: list[dict[str, Any]],
    product_url: str = "",
    human_story: str = "",
) -> dict[str, Any]:
    """Run an evidence-backed audit and return a shareable verification receipt."""
    audit = audit_evidence(
        product_name=product_name,
        description=description,
        evidence=evidence,
        product_url=product_url,
        human_story=human_story,
    )
    receipt = build_public_receipt(audit)
    receipt_signature = sign_document(receipt, purpose="audit_receipt")
    return {
        "receipt": receipt,
        "receipt_signature": receipt_signature,
        "markdown": receipt_markdown(receipt),
        "html": receipt_html(receipt),
    }


@mcp.tool()
def verify_receipt(
    receipt: dict[str, Any],
    receipt_signature: dict[str, Any],
) -> dict[str, Any]:
    """Verify that a receipt was signed by a current or trusted Humanity Score key."""
    signature = str(receipt_signature.get("signature", "")).strip()
    key_id = str(receipt_signature.get("signing_key_id", "")).strip()
    valid = verify_document_signature(
        receipt,
        purpose="audit_receipt",
        signature=signature,
        signing_key_id=key_id,
    )
    return {
        "valid": valid,
        "report_hash": receipt.get("report_hash"),
        "signing_key_id": key_id,
        "signature_algorithm": receipt_signature.get("signature_algorithm", "Ed25519"),
        "notice": (
            "A valid signature attests that the configured Humanity Score key signed this exact receipt. "
            "It does not independently certify the underlying product or replace evidence review."
        ),
    }


@mcp.tool()
def decision_brief(
    product_name: str,
    description: str,
    evidence: list[dict[str, Any]],
    product_url: str = "",
    human_story: str = "",
) -> dict[str, Any]:
    """Return an evidence-backed audit plus actionable decision intelligence."""
    audit = audit_evidence(
        product_name=product_name,
        description=description,
        evidence=evidence,
        product_url=product_url,
        human_story=human_story,
    )
    audit["share_thread"] = share_thread(audit)
    return {
        "audit": audit,
        "decision_intelligence": build_decision_intelligence(audit),
    }


@mcp.tool()
def monitor_product_change(
    product_name: str,
    description: str,
    previous_evidence: list[dict[str, Any]],
    current_evidence: list[dict[str, Any]],
    product_url: str = "",
    human_story: str = "",
) -> dict[str, Any]:
    """Compare two evidence snapshots and report material Humanity Score changes."""
    previous = audit_evidence(
        product_name=product_name,
        description=description,
        evidence=previous_evidence,
        product_url=product_url,
        human_story=human_story,
    )
    current = audit_evidence(
        product_name=product_name,
        description=description,
        evidence=current_evidence,
        product_url=product_url,
        human_story=human_story,
    )
    return {
        "previous_audit": previous,
        "current_audit": current,
        "change_intelligence": compare_audit_results(previous, current),
    }


@mcp.tool()
def snapshot_source(url: str) -> dict[str, Any]:
    """Retrieve a public evidence URL and return bounded snapshot metadata.

    This tool rejects private/local network destinations and returns a SHA-256
    hash plus retrieval timestamp for evidence provenance.
    """
    _enforce_snapshot_rate_limit()
    return retrieve_source_snapshot(url)


@mcp.tool()
def compare_reviews(
    reviewer_a: list[dict[str, Any]],
    reviewer_b: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare two independent Humanity Score evidence-coding passes."""
    return compare_reviewer_evidence(reviewer_a, reviewer_b)


@mcp.tool()
def create_appeal(
    product_name: str,
    report_hash: str,
    appellant: str,
    claim: str,
    evidence_urls: list[str],
    requested_correction: str,
) -> dict[str, Any]:
    """Create a signed appeal record for the caller to submit; this tool does not persist it."""
    appeal = create_appeal_record(
        product_name=product_name,
        report_hash=report_hash,
        appellant=appellant,
        claim=claim,
        evidence_urls=evidence_urls,
        requested_correction=requested_correction,
    )
    return {
        "appeal": appeal,
        "appeal_signature": sign_document(appeal, purpose="appeal_record"),
        "submitted": False,
        "persistence": "none",
        "notice": (
            "This tool prepares and signs an appeal record but does not submit or persist it. "
            "The caller must deliver it through an explicit review channel."
        ),
    }


@mcp.tool()
def procurement_packet(
    product_name: str,
    description: str,
    evidence: list[dict[str, Any]],
    product_url: str = "",
    human_story: str = "",
) -> dict[str, Any]:
    """Run an audit and package it for procurement/governance intake."""
    audit = audit_evidence(
        product_name=product_name,
        description=description,
        evidence=evidence,
        product_url=product_url,
        human_story=human_story,
    )
    return {"audit": audit, "procurement_packet": build_procurement_packet(audit)}


@mcp.tool()
def evidence_requests(
    product_name: str,
    description: str,
    evidence: list[dict[str, Any]],
    product_url: str = "",
    human_story: str = "",
) -> dict[str, Any]:
    """Return targeted evidence requests for missing or weak audit criteria."""
    audit = audit_evidence(
        product_name=product_name,
        description=description,
        evidence=evidence,
        product_url=product_url,
        human_story=human_story,
    )
    return {
        "product_name": product_name,
        "report_hash": audit["report_hash"],
        "requests": evidence_request_checklist(audit),
        "notice": (
            "Requests are due-diligence prompts, not a finding of compliance or non-compliance."
        ),
    }


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
    """Run a backward-compatible self-assessment.

    This path is deliberately self-reported and never badge eligible.
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
    """Generate an UNVERIFIED visual badge for a standalone score."""
    return unverified_badge(product_name, score)


@mcp.tool()
def generate_viral_teardown(product_name: str, score: int) -> dict[str, Any]:
    """Generate conservative share copy without unsupported claims."""
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Humanity Score Checker MCP server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="MCP transport to use (default: stdio)",
    )
    args = parser.parse_args()
    if args.transport == "streamable-http":
        allow_insecure = os.getenv("HUMANITY_SCORE_ALLOW_INSECURE_HTTP", "").strip() == "1"
        if not allow_insecure:
            raise SystemExit(
                "Direct server.py streamable-http is disabled by default because it has no authentication middleware. "
                "Use vercel_app.py for authenticated HTTP, or set HUMANITY_SCORE_ALLOW_INSECURE_HTTP=1 for local/private testing only."
            )
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
