"""
/api/serve_html.py – Dynamic Serverless HTML rewriter for Tweet2Skill.
Injects self-referential og:url & twitter:url with full request path + query string
so X/Twitter card scrapers never canonicalize back to cached failed previews.
"""

from http.server import BaseHTTPRequestHandler
import os
import sys

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            # Determine requesting host and path
            host = self.headers.get("Host", "tweet2skill.hero-apps.com")
            # Enforce non-www HTTPS domain
            if host.startswith("www."):
                host = host[4:]
                
            req_path = self.path if self.path else "/"
            full_url = f"https://{host}{req_path}"

            # Read template HTML
            html_file = os.path.join(os.path.dirname(__file__), "..", "landing-page", "index.html")
            with open(html_file, "r", encoding="utf-8") as f:
                html = f.read()

            # Dynamic replacement of og:url and twitter:url to preserve query string
            html = html.replace('__DYNAMIC_OG_URL__', full_url)

            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "public, max-age=0, must-revalidate")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        except Exception as e:
            print(f"[serve_html] Error serving HTML: {e}", file=sys.stderr)
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Internal Server Error")
