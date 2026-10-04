"""Safe public-source retrieval, provenance attestations, and signing helpers.

Humanity Score never treats caller-supplied hashes as verified evidence. A source
counts as independently retrieved only when its snapshot metadata carries a
valid Ed25519 attestation created by this service.

The fetcher pins the resolved public IP for each request so DNS cannot change
between validation and connection. Redirects are revalidated and pinned again.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import ipaddress
import json
import os
import socket
import ssl
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

MAX_SOURCE_BYTES = 2_000_000
MAX_REDIRECTS = 5
DEFAULT_TIMEOUT_SECONDS = 10
MAX_URL_CHARS = 2048
USER_AGENT = "HumanityScore/3.2 (+https://github.com/oluwafemidiakhoa/humanity-score-checker)"
SIGNING_KEY_ENV = "HUMANITY_SCORE_SIGNING_KEY"


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _load_private_key() -> Ed25519PrivateKey | None:
    raw = os.getenv(SIGNING_KEY_ENV, "").strip()
    if not raw:
        return None

    try:
        if len(raw) == 64 and all(ch in "0123456789abcdefABCDEF" for ch in raw):
            key_bytes = bytes.fromhex(raw)
        else:
            key_bytes = _b64url_decode(raw)
    except Exception as exc:
        raise ValueError(f"{SIGNING_KEY_ENV} is not valid hex/base64url") from exc

    if len(key_bytes) != 32:
        raise ValueError(f"{SIGNING_KEY_ENV} must encode exactly 32 raw Ed25519 private-key bytes")
    return Ed25519PrivateKey.from_private_bytes(key_bytes)


def signing_metadata() -> dict[str, Any]:
    """Return non-secret signing metadata without exposing the private key."""
    try:
        private_key = _load_private_key()
    except ValueError as exc:
        return {"configured": False, "valid": False, "error": str(exc)}

    if private_key is None:
        return {"configured": False, "valid": True, "key_id": None, "public_key": None}

    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_id = hashlib.sha256(public_bytes).hexdigest()[:16]
    return {
        "configured": True,
        "valid": True,
        "key_id": key_id,
        "public_key": _b64url_encode(public_bytes),
        "algorithm": "Ed25519",
    }


def sign_document(payload: dict[str, Any], *, purpose: str) -> dict[str, Any]:
    """Sign a canonical JSON payload with the configured Ed25519 key."""
    private_key = _load_private_key()
    if private_key is None:
        return {
            "signature_status": "unconfigured",
            "signature": "",
            "signing_key_id": "",
            "signing_public_key": "",
            "signature_algorithm": "Ed25519",
        }

    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_id = hashlib.sha256(public_bytes).hexdigest()[:16]
    envelope = {"purpose": purpose, "payload": payload}
    signature = private_key.sign(_canonical_json(envelope))
    return {
        "signature_status": "signed",
        "signature": _b64url_encode(signature),
        "signing_key_id": key_id,
        "signing_public_key": _b64url_encode(public_bytes),
        "signature_algorithm": "Ed25519",
    }


def verify_document_signature(
    payload: dict[str, Any],
    *,
    purpose: str,
    signature: str,
    signing_key_id: str,
) -> bool:
    """Verify a signature against the service's currently configured public key."""
    if not signature or not signing_key_id:
        return False

    metadata = signing_metadata()
    if not metadata.get("configured") or not metadata.get("valid"):
        return False
    if signing_key_id != metadata.get("key_id"):
        return False

    try:
        public_key = Ed25519PublicKey.from_public_bytes(
            _b64url_decode(str(metadata["public_key"]))
        )
        envelope = {"purpose": purpose, "payload": payload}
        public_key.verify(_b64url_decode(signature), _canonical_json(envelope))
    except (InvalidSignature, ValueError, TypeError):
        return False
    return True


def canonical_public_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip() or len(url) > MAX_URL_CHARS:
        raise ValueError("source URL is empty or exceeds the maximum length")

    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("source URL must use http or https")
    if parsed.username or parsed.password:
        raise ValueError("source URL must not contain credentials")
    if not parsed.hostname:
        raise ValueError("source URL must include a hostname")

    host = parsed.hostname.lower().rstrip(".")
    port = parsed.port
    if port and not (
        (parsed.scheme.lower() == "http" and port == 80)
        or (parsed.scheme.lower() == "https" and port == 443)
    ):
        netloc_host = f"[{host}]" if ":" in host else host
        netloc = f"{netloc_host}:{port}"
    else:
        netloc = f"[{host}]" if ":" in host else host

    return urlunparse(
        (
            parsed.scheme.lower(),
            netloc,
            parsed.path or "/",
            "",
            parsed.query,
            "",
        )
    )


def _public_ips(hostname: str, port: int) -> list[str]:
    lowered = hostname.strip().lower().rstrip(".")
    if lowered in {"localhost", "localhost.localdomain"} or lowered.endswith(".local"):
        raise ValueError("private or local source hosts are not allowed")

    try:
        addresses = socket.getaddrinfo(
            lowered,
            port,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as exc:
        raise ValueError(f"source host could not be resolved: {lowered}") from exc

    public: list[str] = []
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
        text = str(ip)
        if text not in public:
            public.append(text)

    if not public:
        raise ValueError("source host did not resolve to a public network address")
    return public


def validate_public_url(url: str) -> str:
    canonical = canonical_public_url(url)
    parsed = urlparse(canonical)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    _public_ips(parsed.hostname or "", port)
    return canonical


def _request_target(parsed) -> str:
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query
    return target


def _host_header(hostname: str, port: int, scheme: str) -> str:
    host = f"[{hostname}]" if ":" in hostname else hostname
    default_port = 443 if scheme == "https" else 80
    return host if port == default_port else f"{host}:{port}"


def _open_pinned(url: str, timeout_seconds: int):
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    scheme = parsed.scheme.lower()
    port = parsed.port or (443 if scheme == "https" else 80)
    ips = _public_ips(hostname, port)
    last_error: Exception | None = None

    for ip in ips:
        sock = None
        conn = None
        try:
            sock = socket.create_connection((ip, port), timeout=timeout_seconds)
            if scheme == "https":
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=hostname)

            conn = http.client.HTTPConnection(ip, port, timeout=timeout_seconds)
            conn.sock = sock
            conn.request(
                "GET",
                _request_target(parsed),
                headers={
                    "Host": _host_header(hostname, port, scheme),
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,text/plain,application/json,application/xml;q=0.8,*/*;q=0.5",
                    "Connection": "close",
                },
            )
            return conn, conn.getresponse()
        except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
            last_error = exc
            if conn is not None:
                conn.close()
            elif sock is not None:
                sock.close()

    raise ValueError(f"source connection failed: {last_error}")


def _read_bounded(response: http.client.HTTPResponse, max_bytes: int) -> bytes:
    declared = response.getheader("Content-Length")
    if declared:
        try:
            if int(declared) > max_bytes:
                raise ValueError(f"source exceeds maximum snapshot size of {max_bytes} bytes")
        except ValueError:
            if declared.isdigit():
                raise

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


def _snapshot_payload(
    *,
    source: str,
    sha256: str,
    retrieved_at: str,
    content_type: str,
    content_length: int,
) -> dict[str, Any]:
    return {
        "schema": "humanity-score.source-snapshot-attestation.v1",
        "source": canonical_public_url(source),
        "source_snapshot_sha256": sha256.lower(),
        "source_retrieved_at": retrieved_at,
        "source_snapshot_content_type": content_type,
        "source_snapshot_bytes": int(content_length),
    }


def verify_snapshot_attestation(item: dict[str, Any]) -> bool:
    """Return True only for a snapshot signed by this deployment's key."""
    try:
        payload = _snapshot_payload(
            source=str(item.get("source", "")),
            sha256=str(item.get("source_snapshot_sha256", "")),
            retrieved_at=str(item.get("source_retrieved_at", "")),
            content_type=str(item.get("source_snapshot_content_type", "")),
            content_length=int(item.get("source_snapshot_bytes", 0)),
        )
    except (TypeError, ValueError):
        return False

    if len(payload["source_snapshot_sha256"]) != 64:
        return False
    try:
        int(payload["source_snapshot_sha256"], 16)
    except ValueError:
        return False
    if payload["source_snapshot_bytes"] <= 0:
        return False
    if not payload["source_snapshot_content_type"]:
        return False
    if not payload["source_retrieved_at"]:
        return False

    return verify_document_signature(
        payload,
        purpose="source_snapshot",
        signature=str(item.get("source_snapshot_signature", "")),
        signing_key_id=str(item.get("source_snapshot_key_id", "")),
    )


def retrieve_source_snapshot(
    url: str,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = MAX_SOURCE_BYTES,
    excerpt_chars: int = 4000,
) -> dict[str, Any]:
    """Fetch a public URL through a pinned public IP and sign its snapshot metadata."""

    if timeout_seconds < 1 or timeout_seconds > 30:
        raise ValueError("timeout_seconds must be between 1 and 30")
    if max_bytes < 1 or max_bytes > MAX_SOURCE_BYTES:
        raise ValueError(f"max_bytes must be between 1 and {MAX_SOURCE_BYTES}")
    if excerpt_chars < 0 or excerpt_chars > 10_000:
        raise ValueError("excerpt_chars must be between 0 and 10000")

    requested_url = validate_public_url(url)
    current_url = requested_url
    final_url = requested_url
    response = None
    body = b""
    content_type = "application/octet-stream"
    charset = "utf-8"

    for redirect_count in range(MAX_REDIRECTS + 1):
        conn = None
        try:
            conn, response = _open_pinned(current_url, timeout_seconds)
            status = int(response.status)

            if status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                if not location:
                    raise ValueError("redirect response is missing a Location header")
                if redirect_count >= MAX_REDIRECTS:
                    raise ValueError("too many redirects")
                current_url = validate_public_url(urljoin(current_url, location))
                continue

            if status < 200 or status >= 300:
                raise ValueError(f"source returned HTTP {status}")

            final_url = canonical_public_url(current_url)
            body = _read_bounded(response, max_bytes)
            content_type = response.headers.get_content_type() or "application/octet-stream"
            charset = response.headers.get_content_charset() or "utf-8"
            break
        except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
            raise ValueError(f"source retrieval failed: {exc}") from exc
        finally:
            if conn is not None:
                conn.close()
    else:
        raise ValueError("source retrieval failed")

    digest = hashlib.sha256(body).hexdigest()
    retrieved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    text_excerpt = ""
    if content_type.startswith("text/") or content_type in {
        "application/json",
        "application/xml",
        "application/xhtml+xml",
    }:
        text_excerpt = body.decode(charset, errors="replace")[:excerpt_chars]

    payload = _snapshot_payload(
        source=final_url,
        sha256=digest,
        retrieved_at=retrieved_at,
        content_type=content_type,
        content_length=len(body),
    )
    signature = sign_document(payload, purpose="source_snapshot")

    evidence_fields = {
        "source": final_url,
        "source_snapshot_sha256": digest,
        "source_retrieved_at": retrieved_at,
        "source_snapshot_content_type": content_type,
        "source_snapshot_bytes": len(body),
        "source_snapshot_signature": signature["signature"],
        "source_snapshot_key_id": signature["signing_key_id"],
    }

    return {
        "requested_url": requested_url,
        "final_url": final_url,
        "source_snapshot_sha256": digest,
        "source_retrieved_at": retrieved_at,
        "content_type": content_type,
        "content_length": len(body),
        "text_excerpt": text_excerpt,
        "signature_status": signature["signature_status"],
        "source_snapshot_signature": signature["signature"],
        "source_snapshot_key_id": signature["signing_key_id"],
        "signing_public_key": signature["signing_public_key"],
        "evidence_fields": evidence_fields,
        "snapshot_notice": (
            "The SHA-256 identifies the exact bytes retrieved through Humanity Score's "
            "public-network-only fetcher. Badge verification requires a valid Humanity Score "
            "Ed25519 attestation. The attestation proves service retrieval, not when the source "
            "first existed; use an external trusted timestamp/archive for independent proof of time."
        ),
    }
