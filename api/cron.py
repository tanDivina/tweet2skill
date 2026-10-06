"""
/api/cron – Vercel Cron heartbeat endpoint to keep Upstash Redis active.
Pings Upstash Redis with a read/write heartbeat operation.
"""

from http.server import BaseHTTPRequestHandler
import json
import time
import sys

from api.lib import upstash


def json_response(handler, status_code, data):
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode("utf-8"))


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            ts = time.time()
            upstash.set("heartbeat:last_cron", str(ts))
            val = upstash.get("heartbeat:last_cron")
            json_response(self, 200, {
                "status": "ok",
                "message": "Heartbeat updated",
                "timestamp": ts,
                "verified": val == str(ts),
            })
        except Exception as e:
            print(f"[cron] Error: {e}", file=sys.stderr)
            json_response(self, 500, {
                "status": "error",
                "message": str(e),
            })
