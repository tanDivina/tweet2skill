"""
JWT and authentication utilities – pure Python stdlib, no dependencies.

Implements HMAC-SHA256 JWT (HS256) creation and verification,
Google OAuth ID-token validation via Google's tokeninfo endpoint,
and request-signature verification.
"""

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.request
import urllib.error


# ── Base64url helpers (RFC 7515) ────────────────────────────────────

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    # Re-add padding
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


# ── JWT (HS256) ─────────────────────────────────────────────────────

def create_jwt(payload: dict, secret: str, expires_in: int = 86400 * 30) -> str:
    """Create a HS256 JWT.

    Args:
        payload: dict of claims (sub, email, tier, etc.)
        secret: HMAC secret string
        expires_in: token lifetime in seconds (default 30 days)

    Returns:
        Signed JWT string.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {**payload, "iat": now, "exp": now + expires_in}

    segments = [
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode()),
        _b64url_encode(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = f"{segments[0]}.{segments[1]}"
    signature = hmac.new(
        secret.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    segments.append(_b64url_encode(signature))

    return ".".join(segments)


def verify_jwt(token: str, secret: str) -> dict:
    """Verify a HS256 JWT and return its payload.

    Raises ValueError on any validation failure.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed JWT: expected 3 segments")

    header_b64, payload_b64, sig_b64 = parts

    # Verify signature
    signing_input = f"{header_b64}.{payload_b64}"
    expected_sig = hmac.new(
        secret.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    actual_sig = _b64url_decode(sig_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid JWT signature")

    # Decode header
    header = json.loads(_b64url_decode(header_b64))
    if header.get("alg") != "HS256":
        raise ValueError(f"Unsupported JWT algorithm: {header.get('alg')}")

    # Decode payload
    payload = json.loads(_b64url_decode(payload_b64))

    # Check expiration
    exp = payload.get("exp")
    if exp is not None and int(exp) < int(time.time()):
        raise ValueError("JWT has expired")

    return payload


# ── Google OAuth ID-token verification ──────────────────────────────

def verify_google_token(id_token: str) -> dict:
    """Verify a Google OAuth ID token by calling Google's tokeninfo endpoint.

    Returns the decoded token payload (sub, email, name, picture, etc.).
    Raises ValueError if the token is invalid or the audience doesn't match.
    """
    google_client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"

    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"Google token verification failed: {error_body}") from exc
    except Exception as exc:
        raise ValueError(f"Google token verification error: {exc}") from exc

    # Audience check – must match our client ID
    if google_client_id and data.get("aud") != google_client_id:
        raise ValueError(
            f"Token audience mismatch: expected {google_client_id}, got {data.get('aud')}"
        )

    # Basic validity
    if not data.get("sub"):
        raise ValueError("Google token missing 'sub' claim")

    return data


# ── Request helpers ─────────────────────────────────────────────────

def get_client_ip(handler) -> str:
    """Extract the real client IP from a BaseHTTPRequestHandler.

    Checks X-Forwarded-For (Vercel/proxy), then X-Real-Ip,
    then falls back to the socket peer address.
    """
    forwarded = handler.headers.get("X-Forwarded-For", "")
    if forwarded:
        # X-Forwarded-For may be "client, proxy1, proxy2"
        return forwarded.split(",")[0].strip()

    real_ip = handler.headers.get("X-Real-Ip", "")
    if real_ip:
        return real_ip.strip()

    # Last resort – direct connection (usually only local dev)
    if hasattr(handler, "client_address") and handler.client_address:
        return handler.client_address[0]

    return "unknown"


def verify_request_signature(handler, body_bytes: bytes) -> bool:
    """Verify the X-Request-Signature HMAC-SHA256 header.

    The signature is computed as HMAC-SHA256(JWT_SECRET, raw_body)
    and sent hex-encoded in X-Request-Signature.

    Returns True if valid or if signature checking is not configured.
    """
    secret = os.environ.get("JWT_SECRET", "")
    if not secret:
        # If no secret is configured, skip validation (dev mode)
        return True

    signature = handler.headers.get("X-Request-Signature", "")
    if not signature:
        return False

    expected = hmac.new(
        secret.encode(), body_bytes, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


def validate_origin(handler) -> bool:
    """Validate that the request Origin is a chrome-extension:// scheme.

    Returns True if valid, or if no Origin header is present (e.g., server-to-server).
    """
    origin = handler.headers.get("Origin", "")
    if not origin:
        # No origin = not a browser request, allow (Vercel cron, webhooks, etc.)
        return True

    return origin.startswith("chrome-extension://")
