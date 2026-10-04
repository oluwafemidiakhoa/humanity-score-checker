"""Render deterministic public Humanity Score audit receipts."""

from __future__ import annotations

import html
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


def build_public_receipt(audit: dict[str, Any], *, audit_date: str | None = None) -> dict[str, Any]:
    required = {
        "product_name", "product_url", "description", "humanity_score",
        "dimension_scores", "criterion_scores", "badge_label", "badge_eligible",
        "evidence_confidence", "evidence_summary", "report_hash", "rubric_version",
        "accepted_evidence", "source_urls", "limitations",
    }
    missing = sorted(required - set(audit))
    if missing:
        raise ValueError(f"Audit is missing receipt fields: {', '.join(missing)}")

    receipt_date = audit_date or date.today().isoformat()
    issued_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "schema": "humanity-score.public-audit-receipt.v3",
        "audit_date": receipt_date,
        "issued_at": issued_at,
        "product": {
            "name": audit["product_name"],
            "url": audit["product_url"],
            "description": audit["description"],
        },
        "result": {
            "humanity_score": audit["humanity_score"],
            "score_status": audit.get("score_status", "scored"),
            "dimension_scores": audit["dimension_scores"],
            "criterion_scores": audit["criterion_scores"],
            "unknown_criteria": audit.get("unknown_criteria", []),
            "coverage_ratio": audit.get("coverage_ratio"),
            "badge_label": audit["badge_label"],
            "badge_eligible": audit["badge_eligible"],
            "evidence_confidence": audit["evidence_confidence"],
        },
        "evidence_summary": audit["evidence_summary"],
        "accepted_evidence": audit["accepted_evidence"],
        "source_urls": audit["source_urls"],
        "source_integrity": audit.get("source_integrity", {}),
        "contradictions": audit.get("contradictions", []),
        "duplicate_evidence": audit.get("duplicate_evidence", []),
        "report_hash": audit["report_hash"],
        "rubric_version": audit["rubric_version"],
        "limitations": audit["limitations"],
        "notice": (
            "Humanity Score is a product-impact rating. It is not a regulatory, legal, "
            "safety, compliance, or government certification."
        ),
    }


def receipt_markdown(receipt: dict[str, Any]) -> str:
    result = receipt["result"]
    dims = result["dimension_scores"]
    score_display = (
        f"{result['humanity_score']}/100"
        if result["humanity_score"] is not None
        else "UNSCORED"
    )
    lines = [
        f'# Humanity Score Audit — {receipt["product"]["name"]}',
        "",
        f'**Audit date:** {receipt["audit_date"]}',
        f'**Issued at:** {receipt["issued_at"]}',
        (
            f'**Humanity Score:** {result["humanity_score"]}/100'
            if result["humanity_score"] is not None
            else '**Humanity Score:** UNSCORED — insufficient evidence'
        ),
        f'**Status:** {result["badge_label"]}',
        f'**Evidence confidence:** {result["evidence_confidence"]}',
        f'**Rubric version:** {receipt["rubric_version"]}',
        f'**Report hash:** `{receipt["report_hash"]}`',
        "", "## Dimension scores", "",
        f'- Agency: {dims["agency"]}/100' if dims["agency"] is not None else '- Agency: UNKNOWN',
        (
            f'- Value Distribution: {dims["value_distribution"]}/100'
            if dims["value_distribution"] is not None else '- Value Distribution: UNKNOWN'
        ),
        (
            f'- Human Connection: {dims["human_connection"]}/100'
            if dims["human_connection"] is not None else '- Human Connection: UNKNOWN'
        ),
        "", "## Evidence", "",
    ]
    for item in receipt["accepted_evidence"]:
        lines.extend([
            f'### {item["dimension"]} / {item["criterion"]}',
            item["finding"], "",
            f'- Source: {item["source"]}',
            f'- Source type: {item["source_type"]}',
            f'- Impact: {item["impact"]}',
            f'- Confidence: {item["confidence"]}',
            f'- Claim ID: {item.get("claim_id", "")}',
            (
                f'- Snapshot SHA-256: {item.get("source_snapshot_sha256")}'
                if item.get("source_snapshot_sha256") else '- Snapshot: not independently preserved'
            ),
            (
                f'- Retrieved at: {item.get("source_retrieved_at")}'
                if item.get("source_retrieved_at") else ''
            ),
            "",
        ])
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in receipt["limitations"])
    lines.extend(["", f'> {receipt["notice"]}', ""])
    return "\n".join(lines)


def receipt_html(receipt: dict[str, Any]) -> str:
    result = receipt["result"]
    dims = result["dimension_scores"]
    score_display = (
        f"{result['humanity_score']}/100"
        if result["humanity_score"] is not None
        else "UNSCORED"
    )
    evidence_html = "".join(
        "<article>"
        + f"<h3>{html.escape(item['dimension'])} / {html.escape(item['criterion'])}</h3>"
        + f"<p>{html.escape(item['finding'])}</p>"
        + f'<p><a href="{html.escape(item["source"], quote=True)}">Source</a> · {html.escape(item["source_type"])} · impact {item["impact"]} · confidence {item["confidence"]}</p>'
        + (
            f'<p>Snapshot SHA-256: <code>{html.escape(item["source_snapshot_sha256"])}</code> · '
            f'retrieved {html.escape(item["source_retrieved_at"])}</p>'
            if item.get("source_snapshot_sha256") and item.get("source_retrieved_at")
            else '<p><em>Source content was not independently preserved for this finding.</em></p>'
        )
        + "</article>"
        for item in receipt["accepted_evidence"]
    )
    limitations = "".join(f"<li>{html.escape(x)}</li>" for x in receipt["limitations"])
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>Humanity Score Audit — {html.escape(receipt['product']['name'])}</title>"
        "<style>body{font-family:system-ui,-apple-system,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;line-height:1.55}"
        ".score{font-size:3rem;font-weight:800}.meta{color:#555}article{border-top:1px solid #ddd;padding:16px 0}"
        "code{word-break:break-all}.dims{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.card{border:1px solid #ddd;border-radius:10px;padding:14px}</style></head><body>"
        f"<h1>Humanity Score Audit — {html.escape(receipt['product']['name'])}</h1>"
        f"<p class=\"score\">{html.escape(score_display)}</p>"
        f"<p><strong>{html.escape(result['badge_label'])}</strong></p>"
        f"<p class=\"meta\">Audit date {html.escape(receipt['audit_date'])} · issued {html.escape(receipt['issued_at'])} · confidence {html.escape(result['evidence_confidence'])} · rubric {html.escape(receipt['rubric_version'])}</p>"
        f"<div class=\"dims\"><div class=\"card\"><strong>Agency</strong><br>{dims['agency'] if dims['agency'] is not None else 'UNKNOWN'}{('/100' if dims['agency'] is not None else '')}</div>"
        f"<div class=\"card\"><strong>Value Distribution</strong><br>{dims['value_distribution'] if dims['value_distribution'] is not None else 'UNKNOWN'}{('/100' if dims['value_distribution'] is not None else '')}</div>"
        f"<div class=\"card\"><strong>Human Connection</strong><br>{dims['human_connection'] if dims['human_connection'] is not None else 'UNKNOWN'}{('/100' if dims['human_connection'] is not None else '')}</div></div>"
        f"<h2>Evidence</h2>{evidence_html}<h2>Verification</h2>"
        f"<p>Report hash: <code>{html.escape(receipt['report_hash'])}</code></p>"
        f"<h2>Limitations</h2><ul>{limitations}</ul><p><strong>{html.escape(receipt['notice'])}</strong></p></body></html>"
    )


def write_receipt_bundle(receipt: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    json_path = path / "receipt.json"
    md_path = path / "README.md"
    html_path = path / "index.html"
    json_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(receipt_markdown(receipt), encoding="utf-8")
    html_path.write_text(receipt_html(receipt), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "html": str(html_path)}
