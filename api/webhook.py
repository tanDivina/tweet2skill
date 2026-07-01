"""
/api/webhook – POST endpoint for Stripe payment webhooks.

Handles subscription lifecycle events:
  - checkout.session.completed  → activate user subscription
  - customer.subscription.updated  → update subscription status (past_due, active, unpaid, trialing)
  - customer.subscription.deleted  → deactivate subscription

Webhook signature is verified using HMAC-SHA256 with STRIPE_WEBHOOK_SECRET.
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


def verify_stripe_signature(body_bytes: bytes, signature_header: str) -> bool:
    """Verify the Stripe webhook HMAC-SHA256 signature."""
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        print("[webhook] WARNING: STRIPE_WEBHOOK_SECRET not configured", file=sys.stderr)
        return False

    if not signature_header:
        return False

    # Stripe-Signature header format: t=1612345678,v1=abcde12345...
    parts = {}
    for item in signature_header.split(","):
        if "=" in item:
            k, v = item.split("=", 1)
            parts[k.strip()] = v.strip()

    t = parts.get("t")
    v1 = parts.get("v1")

    if not t or not v1:
        return False

    # Prevent replay attacks by checking timestamp age (limit to 10 minutes)
    try:
        age = abs(int(time.time()) - int(t))
        if age > 600:
            print(f"[webhook] WARNING: Stripe signature timestamp is expired ({age}s age)", file=sys.stderr)
            return False
    except ValueError:
        return False

    # Construct the signed payload: timestamp + "." + raw_body
    signed_payload = f"{t}.".encode("utf-8") + body_bytes

    expected = hmac.new(
        secret.encode("utf-8"), signed_payload, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, v1)


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            # ── Read body ───────────────────────────────────────────
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)

            # ── Verify signature ────────────────────────────────────
            signature = self.headers.get("Stripe-Signature", "")
            if not signature:
                signature = self.headers.get("stripe-signature", "")

            if not verify_stripe_signature(body_bytes, signature):
                print("[webhook] Stripe signature verification failed", file=sys.stderr)
                json_error(self, 401, "Invalid webhook signature.")
                return

            # ── Parse payload ───────────────────────────────────────
            try:
                payload = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                json_error(self, 400, "Malformed JSON payload.")
                return

            event_type = payload.get("type", "")
            data_object = payload.get("data", {}).get("object", {})

            print(f"[webhook] Received Stripe event: {event_type}", file=sys.stderr)

            # ── Handle checkout.session.completed ───────────────────
            if event_type == "checkout.session.completed":
                # client_reference_id contains the user's secure Google user_id
                user_id = data_object.get("client_reference_id", "")
                subscription_id = data_object.get("subscription", "")
                customer_id = data_object.get("customer", "")
                customer_email = data_object.get("customer_details", {}).get("email", "")

                if not user_id:
                    # Fallback check in metadata
                    user_id = data_object.get("metadata", {}).get("user_id", "")

                if not user_id:
                    print("[webhook] Error: checkout.session.completed has no client_reference_id or user_id", file=sys.stderr)
                    json_response(self, 200, {"status": "ok", "message": "Logged but ignored due to missing user ID reference."})
                    return

                user_key = f"user:{user_id}"
                print(f"[webhook] Activating Pro subscription for User: {user_id}, Sub: {subscription_id}", file=sys.stderr)

                upstash.hset(user_key, "subscription", "active")
                upstash.hset(user_key, "subscription_id", subscription_id)
                upstash.hset(user_key, "stripe_customer_id", customer_id)
                upstash.hset(user_key, "customer_email", customer_email)
                upstash.hset(user_key, "subscription_updated", str(int(time.time())))

                # Set reverse mapping: Stripe Subscription ID -> User ID
                upstash.set(f"sub_to_user:{subscription_id}", user_id)

            # ── Handle customer.subscription.updated ─────────────────
            elif event_type == "customer.subscription.updated":
                subscription_id = data_object.get("id", "")
                stripe_status = data_object.get("status", "")
                cancel_at_period_end = data_object.get("cancel_at_period_end", False)
                current_period_end = data_object.get("current_period_end", 0)

                # Look up user by Subscription ID
                user_id = upstash.get(f"sub_to_user:{subscription_id}")
                if not user_id:
                    print(f"[webhook] Info: No user mapped to subscription ID: {subscription_id}", file=sys.stderr)
                    json_response(self, 200, {"status": "ok", "message": "Ignored subscription update (no mapped user)."})
                    return

                user_key = f"user:{user_id}"
                print(f"[webhook] Updating status for User: {user_id}, Sub: {subscription_id} to Stripe state: {stripe_status}", file=sys.stderr)

                # Map Stripe subscription states to internal states
                if stripe_status in ("active", "trialing"):
                    upstash.hset(user_key, "subscription", "active")
                elif stripe_status in ("past_due", "unpaid", "paused"):
                    upstash.hset(user_key, "subscription", stripe_status)
                else:
                    upstash.hset(user_key, "subscription", "inactive")

                if cancel_at_period_end:
                    upstash.hset(user_key, "subscription_cancels_at", str(current_period_end))
                else:
                    upstash.hdel(user_key, "subscription_cancels_at")

                upstash.hset(user_key, "subscription_updated", str(int(time.time())))

            # ── Handle customer.subscription.deleted ─────────────────
            elif event_type == "customer.subscription.deleted":
                subscription_id = data_object.get("id", "")

                user_id = upstash.get(f"sub_to_user:{subscription_id}")
                if not user_id:
                    print(f"[webhook] Info: No user mapped to subscription ID: {subscription_id} during cancellation", file=sys.stderr)
                    json_response(self, 200, {"status": "ok", "message": "Ignored subscription deletion (no mapped user)."})
                    return

                user_key = f"user:{user_id}"
                print(f"[webhook] Subscription {subscription_id} deleted. Deactivating user {user_id}", file=sys.stderr)

                upstash.hset(user_key, "subscription", "inactive")
                upstash.hdel(user_key, "subscription_cancels_at")
                upstash.hset(user_key, "subscription_updated", str(int(time.time())))

            else:
                print(f"[webhook] Event type '{event_type}' not processed.", file=sys.stderr)

            json_response(self, 200, {"status": "ok"})

        except Exception as e:
            print(f"[webhook] Unexpected error: {e}", file=sys.stderr)
            # Always return 200 to Stripe to prevent retrying on permanent/handled errors
            json_response(self, 200, {"status": "ok", "message": "Processed with errors."})

    def do_OPTIONS(self):
        """Handle CORS preflight requests gracefully."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Stripe-Signature")
        self.end_headers()
