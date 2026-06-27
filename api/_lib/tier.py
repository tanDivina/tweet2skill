"""
Tier detection for Tweet2Skill.

Examines the request to determine the user's tier:
  - pro:  Valid JWT with active subscription
  - byok: User-supplied Gemini API key (no auth required)
  - free: Default – identified by deviceId + IP
"""

import os
from api._lib import auth_utils, upstash


def detect_tier(handler, body: dict = None) -> dict:
    """Detect the caller's tier from request headers and body.

    Priority order:
        1. Authorization: Bearer <jwt> → check subscription → 'pro'
        2. apiKey in body → 'byok'
        3. X-Device-Id header → 'free'
        4. Fallback → 'free' (IP-only)

    Args:
        handler: BaseHTTPRequestHandler instance
        body: parsed JSON body dict (optional, for BYOK key detection)

    Returns:
        {
            tier: 'free' | 'byok' | 'pro',
            userId: str | None,
            deviceId: str | None,
            apiKey: str | None,       # only set for BYOK
            email: str | None,        # only set for Pro
        }
    """
    result = {
        "tier": "free",
        "userId": None,
        "deviceId": None,
        "apiKey": None,
        "email": None,
    }

    body = body or {}

    # ── 1. Check JWT for Pro tier ───────────────────────────────────
    auth_header = handler.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        jwt_secret = os.environ.get("JWT_SECRET", "")

        if jwt_secret and token:
            try:
                payload = auth_utils.verify_jwt(token, jwt_secret)
                user_id = payload.get("sub", "")
                email = payload.get("email", "")

                if user_id:
                    # OWNER BYPASS: ensure dorien.vda@gmail.com always gets Pro
                    if email == "dorien.vda@gmail.com":
                        result["tier"] = "pro"
                        result["userId"] = user_id
                        result["email"] = email
                        return result

                    # Check if user has active subscription in Redis
                    sub_status = upstash.hget(f"user:{user_id}", "subscription")

                    if sub_status == "active":
                        result["tier"] = "pro"
                        result["userId"] = user_id
                        result["email"] = email
                        return result
                    else:
                        # Valid JWT but no active subscription – fall through
                        # They can still use free tier with their userId
                        result["userId"] = user_id
                        result["email"] = email
            except (ValueError, Exception):
                # Invalid JWT – ignore and fall through to lower tiers
                pass

    # ── 2. Check for BYOK (user-supplied API key) ───────────────────
    api_key = body.get("apiKey", "")
    if api_key:
        result["tier"] = "byok"
        result["apiKey"] = api_key
        # BYOK users may also have a deviceId for tracking
        result["deviceId"] = handler.headers.get("X-Device-Id", "")
        return result

    # ── 3. Free tier – use deviceId from header ─────────────────────
    device_id = handler.headers.get("X-Device-Id", "")
    result["deviceId"] = device_id if device_id else None

    return result
