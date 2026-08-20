"""
/api/usage – GET endpoint returning usage counts for the current user/device.

Query params:
  - deviceId (optional): for free-tier usage lookup
  - (or) Authorization header with JWT for Pro user lookup

Response:
  {
    tier: 'free' | 'byok' | 'pro',
    daily: { used, limit, remaining },
    monthly: { used, limit, remaining }
  }
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys

from api.lib import auth_utils, rate_limiter, upstash
from api.lib.auth_utils import verify_jwt


def json_response(handler, status_code, data):
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode("utf-8"))


def json_error(handler, status_code, message):
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(
        json.dumps({"status": "error", "message": message}).encode("utf-8")
    )


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, X-Device-Id",
        )
        self.end_headers()

    def do_GET(self):
        try:
            # ── Parse query params ──────────────────────────────────
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            device_id = params.get("deviceId", [None])[0]

            # ── Check for authenticated user ────────────────────────
            auth_header = self.headers.get("Authorization", "")
            jwt_secret = os.environ.get("JWT_SECRET", "")
            user_id = None
            tier = "free"
            sub_status = "none"
            credits_val = 0

            if auth_header.startswith("Bearer ") and jwt_secret:
                token = auth_header[7:].strip()
                try:
                    payload = verify_jwt(token, jwt_secret)
                    user_id = payload.get("sub")
                    email = payload.get("email")

                    if email == "dorien.vda@gmail.com":
                        tier = "pro"
                        sub_status = "active"
                    else:
                        user_data = upstash.hgetall(f"user:{user_id}")
                        sub_status = user_data.get("subscription", "none")
                        try:
                            credits_val = int(user_data.get("credits", "0"))
                        except ValueError:
                            credits_val = 0

                        if sub_status in ("active", "pro") or credits_val > 0:
                            tier = "pro"
                        else:
                            tier = "free"
                except ValueError:
                    pass  # Invalid JWT – fall through to free tier

            # ── Build usage response ────────────────────────────────
            daily_limit = 3
            weekly_limit = 10
            daily_used = 0
            weekly_used = 0
            legacy_monthly_used = 0

            try:
                if tier == "pro" and user_id:
                    legacy_monthly_used = rate_limiter.get_monthly_usage(user_id)
                else:
                    client_ip = auth_utils.get_client_ip(self)
                    identifier = f"dev:{device_id}" if device_id else f"ip:{client_ip}"
                    daily_used = rate_limiter.get_daily_usage(identifier)
                    weekly_used = rate_limiter.get_weekly_usage(identifier)
            except Exception as e:
                # Fallback to zeroed usage when Redis is down
                print(f"[usage] Redis lookup error, falling back to 0: {e}", file=sys.stderr)

            if tier == "pro" and user_id:
                response_data = {
                    "status": "ok",
                    "tier": "pro",
                    "subscription": sub_status,
                    "credits": {
                        "remaining": credits_val,
                    },
                    "daily": {
                        "used": None,
                        "limit": None,
                        "remaining": None,
                    },
                    "weekly": {
                        "used": None,
                        "limit": None,
                        "remaining": None,
                    },
                }
                # For backward-compatibility with legacy extension installations
                if sub_status == "active":
                    response_data["monthly"] = {
                        "used": legacy_monthly_used,
                        "limit": 1250,
                        "remaining": max(0, 1250 - legacy_monthly_used),
                    }
                else:
                    response_data["monthly"] = {
                        "used": None,
                        "limit": None,
                        "remaining": None,
                    }
                json_response(self, 200, response_data)
            else:
                json_response(self, 200, {
                    "status": "ok",
                    "tier": "free",
                    "daily": {
                        "used": daily_used,
                        "limit": daily_limit,
                        "remaining": max(0, daily_limit - daily_used),
                    },
                    "weekly": {
                        "used": weekly_used,
                        "limit": weekly_limit,
                        "remaining": max(0, weekly_limit - weekly_used),
                    },
                    "monthly": {
                        "used": None,
                        "limit": None,
                        "remaining": None,
                    },
                })

        except Exception as e:
            print(f"[usage] Error: {e}", file=sys.stderr)
            json_error(self, 500, "Internal server error.")
