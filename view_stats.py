#!/usr/bin/env python3
"""
Tweet2Skill — Admin Stats & Usage Inspector
Run this script anytime to see a summary of registered users, cloud usage, and feedback.
"""

import os
import sys
import json
from datetime import datetime

# Load environment variables
for ef in [".env.local", ".env"]:
    if os.path.exists(ef):
        with open(ef) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

try:
    from api.lib import upstash
except ImportError:
    print("Error: Could not import api.lib.upstash. Run from project root.")
    sys.exit(1)

def inspect():
    print("=" * 60)
    print(" 🚀 Tweet2Skill — Live Usage & User Dashboard")
    print("=" * 60)

    # 1. Registered Users
    user_keys = upstash._execute(["KEYS", "user:*"]) or []
    print(f"\n👥 Registered Cloud Users ({len(user_keys)}):")
    print("-" * 60)
    
    for uk in user_keys:
        raw = upstash._execute(["HGETALL", uk]) or []
        user_data = dict(zip(raw[0::2], raw[1::2]))
        email = user_data.get("email", "Unknown")
        name = user_data.get("name", "N/A")
        sub = user_data.get("subscription", "free")
        credits = user_data.get("credits", "N/A")
        created = user_data.get("created_at", "")
        created_str = datetime.fromtimestamp(int(created)).strftime("%Y-%m-%d %H:%M") if created and created.isdigit() else "N/A"
        
        print(f" • {email:<30} | Name: {name:<18} | Tier: {sub:<6} | Credits: {credits} | Joined: {created_str}")

    # 2. Usage Keys
    usage_keys = upstash._execute(["KEYS", "usage:*"]) or []
    monthly_keys = upstash._execute(["KEYS", "monthly:*"]) or []
    
    print(f"\n📊 Active Usage Records ({len(usage_keys)} daily, {len(monthly_keys)} monthly):")
    print("-" * 60)
    for mk in monthly_keys:
        val = upstash._execute(["GET", mk])
        print(f" • Month count: {mk} => {val} generations")

    # 3. Feedbacks
    feedbacks = upstash._execute(["LRANGE", "feedbacks", "0", "-1"]) or []
    print(f"\n💬 Feedback Submissions ({len(feedbacks)}):")
    print("-" * 60)
    if not feedbacks:
        print(" (No user feedback submitted yet)")
    else:
        for idx, fb_raw in enumerate(feedbacks, 1):
            try:
                fb = json.loads(fb_raw)
                ts = datetime.fromtimestamp(fb.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M")
                print(f" [{idx}] {ts} | {fb.get('type','').upper()} from {fb.get('email','Anonymous')}:")
                print(f"     \"{fb.get('message', '')}\"")
            except Exception:
                print(f" [{idx}] {fb_raw}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    inspect()
