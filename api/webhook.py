"""
/api/webhook – POST endpoint for Lemon Squeezy payment webhooks.

Handles subscription lifecycle events:
  - subscription_created  → activate user subscription
  - subscription_updated  → update subscription status
  - subscription_cancelled → mark subscription as cancelled (stays active until period end)
  - subscription_expired   → deactivate subscription

Webhook signature is verified using HMAC-SHA256 with LEMON_SQUEEZY_WEBHOOK_SECRET.
"""

from http.server import BaseHTTPRequestHandler
import hashlib
import hmac
import json
import os
import sys
import time

from api._lib import upstash


def json_response(handler, status_code, data):
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode("utf-8"))


def json_error(handler, status_code, message):
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(
        json.dumps({"status": "error", "message": message}).encode("utf-8")
    )


def verify_webhook_signature(body_bytes: bytes, signature: str) -> bool:
    """Verify the Lemon Squeezy webhook HMAC-SHA256 signature."""
    secret = os.environ.get("LEMON_SQUEEZY_WEBHOOK_SECRET", "")
    if not secret:
        print("[webhook] WARNING: No webhook secret configured", file=sys.stderr)
        return False

    expected = hmac.new(
        secret.encode(), body_bytes, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            # ── Read body ───────────────────────────────────────────
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)

            # ── Verify signature ────────────────────────────────────
            signature = self.headers.get("X-Signature", "")
            if not signature:
                signature = self.headers.get("x-signature", "")

            if not verify_webhook_signature(body_bytes, signature):
                print("[webhook] Signature verification failed", file=sys.stderr)
                json_error(self, 401, "Invalid webhook signature.")
                return

            # ── Parse payload ───────────────────────────────────────
            try:
                payload = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                json_error(self, 400, "Malformed JSON payload.")
                return

            # Lemon Squeezy webhook structure:
            # {
            #   "meta": { "event_name": "subscription_created", "custom_data": { "user_id": "..." } },
            #   "data": { "id": "...", "attributes": { "status": "active", ... } }
            # }

            meta = payload.get("meta", {})
            event_name = meta.get("event_name", "")
            custom_data = meta.get("custom_data", {})
            user_id = custom_data.get("user_id", "")

            data = payload.get("data", {})
            attributes = data.get("attributes", {})
            subscription_id = str(data.get("id", ""))
            ls_status = attributes.get("status", "")

            print(
                f"[webhook] Event: {event_name}, User: {user_id}, "
                f"Sub: {subscription_id}, Status: {ls_status}",
                file=sys.stderr,
            )

            if not user_id:
                # Try to look up user by subscription ID
                stored_user = upstash.get(f"sub_to_user:{subscription_id}")
                if stored_user:
                    user_id = stored_user
                else:
                    print(f"[webhook] No user_id for event {event_name}", file=sys.stderr)
                    # Still return 200 so Lemon Squeezy doesn't retry
                    json_response(self, 200, {"status": "ok", "message": "No user_id found, event logged."})
                    return

            user_key = f"user:{user_id}"

            # ── Handle events ───────────────────────────────────────

            if event_name == "subscription_created":
                upstash.hset(user_key, "subscription", "active")
                upstash.hset(user_key, "subscription_id", subscription_id)
                upstash.hset(user_key, "subscription_updated", str(int(time.time())))
                # Reverse mapping: subscription → user
                upstash.set(f"sub_to_user:{subscription_id}", user_id)

            elif event_name == "subscription_updated":
                # Map Lemon Squeezy statuses to our internal status
                if ls_status in ("active", "trialing"):
                    upstash.hset(user_key, "subscription", "active")
                elif ls_status in ("past_due", "paused"):
                    upstash.hset(user_key, "subscription", ls_status)
                elif ls_status in ("cancelled", "expired", "unpaid"):
                    upstash.hset(user_key, "subscription", "inactive")
                else:
                    upstash.hset(user_key, "subscription", ls_status)

                upstash.hset(user_key, "subscription_updated", str(int(time.time())))

            elif event_name == "subscription_cancelled":
                # Cancelled = still active until period end
                # Lemon Squeezy sends subscription_expired when it actually ends
                ends_at = attributes.get("ends_at", "")
                upstash.hset(user_key, "subscription", "active")  # still active
                upstash.hset(user_key, "subscription_cancels_at", ends_at)
                upstash.hset(user_key, "subscription_updated", str(int(time.time())))

            elif event_name in ("subscription_expired", "subscription_payment_failed"):
                upstash.hset(user_key, "subscription", "inactive")
                upstash.hset(user_key, "subscription_updated", str(int(time.time())))

            elif event_name == "subscription_resumed":
                upstash.hset(user_key, "subscription", "active")
                upstash.hset(user_key, "subscription_updated", str(int(time.time())))

            else:
                print(f"[webhook] Unhandled event: {event_name}", file=sys.stderr)

            json_response(self, 200, {"status": "ok"})

        except Exception as e:
            print(f"[webhook] Error: {e}", file=sys.stderr)
            # Always return 200 to prevent Lemon Squeezy from retrying on server errors
            # that aren't transient (better to log and investigate)
            json_response(self, 200, {"status": "ok", "message": "Event processed with errors."})
