#!/usr/bin/env python3
"""
view_feedbacks.py – Simple CLI tool to pull and beautifully display feedback submissions from the Upstash Redis feedbacks list.
"""

import os
import json
from datetime import datetime

# Load environment variables from .env.local or .env.production
def load_env():
    for env_file in ['.env.local', '.env.production']:
        if os.path.exists(env_file):
            print(f"Loading credentials from {env_file}...")
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        # Strip optional quotes
                        v = v.strip().strip("'").strip('"')
                        os.environ[k.strip()] = v
            break

load_env()

# Import upstash after setting env vars
try:
    from api._lib import upstash
except ImportError:
    print("Error: Could not import api._lib.upstash. Make sure you run this script from the project root.")
    exit(1)

def get_feedbacks():
    # Fetch all items from 'feedbacks' list using LRANGE feedbacks 0 -1
    raw_list = upstash._execute(["LRANGE", "feedbacks", "0", "-1"])
    if not raw_list:
        print("\nNo feedbacks found in Redis feedbacks list.")
        return

    print(f"\nFound {len(raw_list)} feedback submissions:\n")
    print("=" * 80)
    for i, raw_item in enumerate(raw_list, 1):
        try:
            item = json.loads(raw_item)
            timestamp = item.get("timestamp", 0)
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            fb_type = item.get("type", "unknown").upper()
            email = item.get("email", "Anonymous")
            device_id = item.get("deviceId", "Unknown")
            message = item.get("message", "")
            context = item.get("context", {})
            source = context.get("source", "Unknown")
            tab_url = context.get("tabUrl", "N/A")
            
            type_symbol = "🐞" if fb_type == "BUG" else "💡"
            
            print(f"[{i}] {type_symbol} {fb_type} | Submitted at: {date_str}")
            print(f"    From: {email} (Device: {device_id})")
            print(f"    Source: {source} | URL: {tab_url}")
            print("-" * 80)
            print(f"    Feedback details:\n\n{message}\n")
            print("=" * 80)
        except Exception as e:
            print(f"[{i}] Failed to parse feedback item: {str(e)}")
            print(f"    Raw content: {raw_item}")
            print("=" * 80)

if __name__ == "__main__":
    get_feedbacks()
