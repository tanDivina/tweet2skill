#!/usr/bin/env python3
"""
Test script for Stripe Webhook Signature Verification.
"""

import hmac
import hashlib
import time
import os
import sys

# Add parent dir to path so we can import verify_stripe_signature
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.webhook import verify_stripe_signature


def run_test():
    secret = "whsec_test_secret_12345"
    os.environ["STRIPE_WEBHOOK_SECRET"] = secret

    # Simulated raw body bytes
    body_bytes = b'{"id": "evt_123", "type": "checkout.session.completed"}'
    t = str(int(time.time()))

    # Construct signature payload: timestamp + "." + body
    signed_payload = f"{t}.".encode("utf-8") + body_bytes

    # Calculate expected signature v1
    v1 = hmac.new(
        secret.encode("utf-8"), signed_payload, hashlib.sha256
    ).hexdigest()

    signature_header = f"t={t},v1={v1}"

    print(f"Testing signature verification...")
    print(f"Timestamp: {t}")
    print(f"v1: {v1}")
    print(f"Header: {signature_header}")

    # Call verify function
    is_valid = verify_stripe_signature(body_bytes, signature_header)

    print(f"Result: {is_valid}")
    assert is_valid is True, "Verification failed for valid signature!"
    print("SUCCESS: Valid signature verified successfully!")

    # Test expired timestamp
    old_t = str(int(time.time()) - 1000)  # > 600s
    old_signed_payload = f"{old_t}.".encode("utf-8") + body_bytes
    old_v1 = hmac.new(
        secret.encode("utf-8"), old_signed_payload, hashlib.sha256
    ).hexdigest()
    old_header = f"t={old_t},v1={old_v1}"

    is_valid_old = verify_stripe_signature(body_bytes, old_header)
    print(f"Result for expired timestamp: {is_valid_old}")
    assert is_valid_old is False, "Verification should have failed for expired timestamp!"
    print("SUCCESS: Expired signature failed verification as expected!")


if __name__ == "__main__":
    run_test()
