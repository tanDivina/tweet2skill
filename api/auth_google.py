"""
/api/auth_google – POST endpoint for Google OAuth sign-in.

Accepts a Google OAuth ID token, verifies it via Google's tokeninfo endpoint,
creates or updates the user record in Redis, and returns a signed JWT.

Request body:
  { "idToken": "<google_id_token>" }

Response:
  {
    "status": "ok",
    "token": "<jwt>",
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
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, X-Device-Id",
        )
        self.end_headers()

    def do_POST(self):
        try:
            # ── Read body ───────────────────────────────────────────
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)

            try:
                payload = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                json_error(self, 400, "Malformed JSON payload.")
                return

            id_token = payload.get("idToken", "")
            if not id_token:
                json_error(self, 400, "Missing idToken in request body.")
                return

            # ── Verify Google ID token ──────────────────────────────
            try:
                google_data = auth_utils.verify_google_token(id_token)
            except ValueError as e:
                json_error(self, 401, f"Google authentication failed: {e}")
                return

            google_id = google_data.get("sub", "")
            email = google_data.get("email", "")
            name = google_data.get("name", google_data.get("given_name", ""))
            picture = google_data.get("picture", "")

            if not google_id:
                json_error(self, 401, "Could not extract user ID from Google token.")
                return

            # ── Create/update user in Redis ─────────────────────────
            user_key = f"user:{google_id}"

            # Check if user already exists
            existing = upstash.hgetall(user_key)

            if not existing:
                # New user – create record
                upstash.hset(user_key, "email", email)
                upstash.hset(user_key, "name", name)
                upstash.hset(user_key, "picture", picture)
                upstash.hset(user_key, "subscription", "none")
                upstash.hset(user_key, "created_at", str(int(__import__("time").time())))
                subscription_status = "none"
            else:
                # Existing user – update profile fields (name/picture may change)
                upstash.hset(user_key, "email", email)
                upstash.hset(user_key, "name", name)
                upstash.hset(user_key, "picture", picture)
                subscription_status = existing.get("subscription", "none")

            # ── Determine tier ──────────────────────────────────────
            if email == "dorien.vda@gmail.com":
                subscription_status = "active"
                
            tier = "pro" if subscription_status == "active" else "free"

            # ── Create JWT ──────────────────────────────────────────
            jwt_secret = os.environ.get("JWT_SECRET", "")
            if not jwt_secret:
                json_error(self, 500, "Server authentication not configured.")
                return

            jwt_payload = {
                "sub": google_id,
                "email": email,
                "name": name,
                "tier": tier,
            }
            token = auth_utils.create_jwt(jwt_payload, jwt_secret)

            # ── Return response ─────────────────────────────────────
            json_response(self, 200, {
                "status": "ok",
                "token": token,
                "user": {
                    "id": google_id,
                    "email": email,
                    "name": name,
                    "picture": picture,
                    "tier": tier,
                },
            })

        except Exception as e:
            print(f"[auth_google] Error: {e}", file=sys.stderr)
            json_error(self, 500, "Internal server error.")
