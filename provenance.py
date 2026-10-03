"""Safe public-source retrieval and snapshot hashing for Humanity Score.

This module intentionally rejects localhost/private/reserved destinations,
limits redirects, imposes a response-size cap, and returns only a bounded text
excerpt plus cryptographic metadata. It is designed for public evidence URLs,
not authenticated or internal resources.
"""

from __future__ import annotations

import hashlib
import ipaddress
import socket
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_SOURCE_BYTES = 2_000_000
MAX_REDIRECTS = 5
DEFAULT_TIMEOUT_SECONDS = 10
USER_AGENT = "HumanityScore/3.1 (+https://github.com/oluwafemidiakhoa/humanity-score-checker)"


def _reject_non_public_host(hostname: str) -> None:
    if not hostname:
        raise ValueError("source URL must include a hostname")

    lowered = hostname.strip().lower().rstrip(".")
    if lowered in {"localhost", "localhost.localdomain"} or lowered.endswith(".local"):
        raise ValueError("private or local source hosts are not allowed")

    try:
        addresses = socket.getaddrinfo(lowered, None)
    except socket.gaierror as exc:
        raise ValueError(f"source host could not be resolved: {lowered}") from exc

    for result in addresses:
        raw = result[4][0]
        ip = ipaddress.ip_address(raw)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ValueError("source host resolves to a non-public network address")


def validate_public_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("source URL must use http or https")
    if parsed.username or parsed.password:
        raise ValueError("source URL must not contain credentials")
    _reject_non_public_host(parsed.hostname or "")
    return parsed.geturl()


class _SafeRedirectHandler(HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirect_count += 1
        if self.redirect_count > MAX_REDIRECTS:
            raise HTTPError(newurl, code, "too many redirects", headers, fp)
        resolved = urljoin(req.full_url, newurl)
        validate_public_url(resolved)
        return super().redirect_request(req, fp, code, msg, headers, resolved)


def _read_bounded(response, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(min(65536, max_bytes + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise ValueError(f"source exceeds maximum snapshot size of {max_bytes} bytes")
    return b"".join(chunks)


def retrieve_source_snapshot(
    url: str,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = MAX_SOURCE_BYTES,
    excerpt_chars: int = 4000,
) -> dict[str, Any]:
    """Fetch a public URL and return snapshot metadata for audit provenance."""

    requested_url = validate_public_url(url)
    opener = build_opener(_SafeRedirectHandler())
    request = Request(
        requested_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,text/plain,application/json,application/xml;q=0.8,*/*;q=0.5",
        },
        method="GET",
    )

    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            final_url = validate_public_url(response.geturl())
            body = _read_bounded(response, max_bytes)
            content_type = response.headers.get_content_type()
            charset = response.headers.get_content_charset() or "utf-8"
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise ValueError(f"source retrieval failed: {exc}") from exc

    digest = hashlib.sha256(body).hexdigest()
    retrieved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    text_excerpt = ""
    if content_type.startswith("text/") or content_type in {
        "application/json",
        "application/xml",
        "application/xhtml+xml",
    }:
        text_excerpt = body.decode(charset, errors="replace")[:excerpt_chars]

    return {
        "requested_url": requested_url,
        "final_url": final_url,
        "source_snapshot_sha256": digest,
        "source_retrieved_at": retrieved_at,
        "content_type": content_type,
        "content_length": len(body),
        "text_excerpt": text_excerpt,
        "snapshot_notice": (
            "The SHA-256 identifies the bytes retrieved by this tool. For independent "
            "proof of time, persist the snapshot or hash in a trusted timestamp/archive service."
        ),
    }
