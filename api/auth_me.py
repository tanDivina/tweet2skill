"""
/api/auth_me – GET endpoint for retrieving the current user profile.

Requires Authorization: Bearer <jwt> header.

Response:
  {
    "status": "ok",
    "user": { "id": "...", "email": "...", "name": "...", "picture": "...", "tier": "..." }
  }
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys

from api._lib import auth_utils, upstash


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
            "Content-Type, Authorization",
        )
        self.end_headers()

    def do_GET(self):
        try:
            # ── Verify JWT ──────────────────────────────────────────
            auth_header = self.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                json_error(self, 401, "Missing or invalid Authorization header.")
                return

            token = auth_header[7:].strip()
            jwt_secret = os.environ.get("JWT_SECRET", "")
            if not jwt_secret:
                json_error(self, 500, "Server authentication not configured.")
                return

            try:
                payload = auth_utils.verify_jwt(token, jwt_secret)
            except ValueError as e:
                json_error(self, 401, f"Invalid token: {e}")
                return

            user_id = payload.get("sub", "")
            if not user_id:
                json_error(self, 401, "Token missing user identity.")
                return

            # ── Fetch user from Redis ───────────────────────────────
            user_data = upstash.hgetall(f"user:{user_id}")
            if not user_data:
                json_error(self, 404, "User not found.")
                return

            subscription = user_data.get("subscription", "none")
            tier = "pro" if subscription == "active" else "free"

            json_response(self, 200, {
                "status": "ok",
                "user": {
                    "id": user_id,
                    "email": user_data.get("email", ""),
                    "name": user_data.get("name", ""),
                    "picture": user_data.get("picture", ""),
                    "tier": tier,
                    "subscription": subscription,
                },
            })

        except Exception as e:
            print(f"[auth_me] Error: {e}", file=sys.stderr)
            json_error(self, 500, "Internal server error.")
