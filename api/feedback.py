"""
/api/feedback – POST endpoint to submit user feedback, suggestions, and bug reports.

Accepts bug reports or feature suggestions from either the extension or the website,
captures system context, and saves them directly to the feedbacks queue in Redis.

Request body:
  {
    "type": "bug" | "suggestion",
    "message": "...",
    "email": "..." (optional),
    "deviceId": "..." (optional),
    "context": { ... } (optional, browser/system metadata)
  }
"""

from http.server import BaseHTTPRequestHandler
import json
import time

from api._lib import upstash, auth_utils


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

            feedback_type = payload.get("type", "").strip().lower()
            message = payload.get("message", "").strip()
            email = payload.get("email", "").strip()
            device_id = payload.get("deviceId", "").strip() or self.headers.get("X-Device-Id", "").strip()
            context = payload.get("context", {})

            if not feedback_type or feedback_type not in ["bug", "suggestion"]:
                json_error(self, 400, "Feedback type must be 'bug' or 'suggestion'.")
                return

            if not message:
                json_error(self, 400, "Feedback message cannot be empty.")
                return

            # Max message limit to prevent database flooding
            if len(message) > 5000:
                json_error(self, 400, "Feedback message exceeds 5000 characters limit.")
                return

            # Capture additional network-level environment details safely
            user_agent = self.headers.get("User-Agent", "Unknown")
            client_ip = auth_utils.get_client_ip(self)

            # Build standardized, searchable feedback structure
            feedback_payload = {
                "type": feedback_type,
                "message": message,
                "email": email or "Anonymous",
                "deviceId": device_id or "Unknown",
                "timestamp": int(time.time()),
                "ip": client_ip,
                "userAgent": user_agent,
                "context": context
            }

            # Append directly to Redis list 'feedbacks'
            upstash.rpush("feedbacks", json.dumps(feedback_payload))

            # Dispatch instant email notification via FormSubmit.co
            send_formsubmit_email(feedback_type, message, email, context, client_ip)

            json_response(self, 200, {
                "status": "ok",
                "message": "Feedback submitted successfully! Thank you."
            })

        except Exception as e:
            json_error(self, 500, f"Internal server error: {str(e)}")


def send_formsubmit_email(feedback_type, message, email, context, client_ip):
    """Dispatches instant email notification to support@hero-apps.com via FormSubmit."""
    import urllib.request
    import urllib.error
    try:
        url = "https://formsubmit.co/ajax/support@hero-apps.com"
        subject = f"[Tweet2Skill] New {feedback_type.capitalize()} Submission"
        
        form_data = {
            "_subject": subject,
            "Category": feedback_type.capitalize(),
            "Message": message,
            "User Email": email or "Anonymous",
            "Page URL": context.get("tabUrl", "https://tweet2skill.hero-apps.com"),
            "Source": context.get("source", "landing-page"),
            "Client IP": client_ip,
            "_captcha": "false"
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(form_data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Referer": "https://tweet2skill.hero-apps.com/",
                "Origin": "https://tweet2skill.hero-apps.com",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception as err:
        print(f"FormSubmit dispatch notice: {err}")

