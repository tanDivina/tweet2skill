from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import re

def slugify(text):
    """Convert text into a clean folder name slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\-]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def call_gemini_api(api_key, content, source_url, agent_system="antigravity"):
    """Send text to the Gemini API and return the generated skill or rule markdown."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    if agent_system == "claude":
        system_prompt = (
            "You are a Claude Code custom rule generator. Take the provided web or tweet content "
            "and convert it into a structured Markdown block representing a Claude Code development rule or guideline.\n\n"
            "The output must exactly follow this format:\n"
            "# [Rule Title]\n\n"
            "[Brief description of what this rule is and when it applies. Keep it extremely concise.]\n\n"
            "## Instructions / Guidelines\n"
            "[Convert the core guidelines, prompts, coding patterns, or rules into precise, clean, action-oriented instructions for the Claude Code CLI agent.]\n\n"
            "CRITICAL RULES:\n"
            "1. DO NOT include any YAML frontmatter or triple-dashes (---).\n"
            "2. DO NOT wrap the output in ```markdown or ``` block code fences.\n"
            "3. Do not add any conversational text before or after the markdown block."
        )
    else:
        system_prompt = (
            "You are an Antigravity Skill generator. Take the provided web or tweet content "
            "and convert it into a structured Markdown block representing an Antigravity agent skill.\n\n"
            "The output must exactly follow this format, including the YAML frontmatter (between triple-dashes):\n"
            "---\n"
            "name: [Short, clear, lowercase, kebab-case action-oriented skill name matching directory slug]\n"
            "description: [One or two sentences explaining exactly WHEN the agent should trigger and use this skill]\n"
            "---\n\n"
            "# [Skill Name in Title Case]\n\n"
            "[Brief description of what this skill does and when to use it.]\n\n"
            "## Instructions\n"
            "[Convert the core rules, steps, or prompts in the provided content into precise, clean, action-oriented agent guidelines.]\n\n"
            "CRITICAL RULES:\n"
            "1. Start the response directly with the triple-dashes (---). DO NOT wrap your output in ```markdown or ``` block code fences.\n"
            "2. Do not add any conversational text before or after the markdown block."
        )

    user_prompt = f"Source URL: {source_url}\n\nRaw Content:\n{content}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": user_prompt}
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": system_prompt}
            ]
        },
        "generationConfig": {
            "temperature": 0.2
        }
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if not candidates:
                raise ValueError("No API response candidates returned.")
            
            text = candidates[0].get("content", {}).get("parts", [])[0].get("text", "")
            return text
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("error", {}).get("message", "HTTP Error")
            raise Exception(f"Gemini API Error: {msg}")
        except json.JSONDecodeError:
            raise Exception(f"Gemini API returned status {e.code}: {e.reason}")
    except Exception as e:
        raise e

def clean_markdown(text):
    """Strip code block wrappers if the model wrapped its output in fences."""
    text = text.strip()
    text = re.sub(r"^```markdown\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        # 1. Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            payload = json.loads(post_data.decode('utf-8'))
        except Exception:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "Malformed JSON payload."}).encode('utf-8'))
            return

        url = payload.get("url", "")
        title = payload.get("title", "")
        content = payload.get("content", "")
        api_key = payload.get("apiKey", "")
        agent_system = payload.get("agentSystem", "antigravity")

        if not api_key:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "API key missing in request."}).encode('utf-8'))
            return

        if not content:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "Content to process is empty."}).encode('utf-8'))
            return

        try:
            # 2. Call Gemini API
            generated_content = call_gemini_api(api_key, content, url, agent_system)
            generated_content = clean_markdown(generated_content)

            # 3. Extract title/slug for the download filename
            if agent_system == "claude":
                title_match = re.search(r"^#\s*([^\n]+)", generated_content, re.MULTILINE)
                rule_title = title_match.group(1).strip() if title_match else (title or "custom-rule")
                slug_name = slugify(rule_title) or "custom-rule"
                filename = f"{slug_name}.md"
            else:
                name_match = re.search(r"^name:\s*([^\n]+)", generated_content, re.MULTILINE)
                skill_name = name_match.group(1).strip().strip('"').strip("'") if name_match else (slugify(title) or "custom-skill")
                slug_name = slugify(skill_name) or "custom-skill"
                filename = "SKILL.md" # For Antigravity it is always saved inside skills/slug/SKILL.md

            # 4. Respond with generated markdown
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_payload = {
                "status": "done",
                "markdown": generated_content,
                "filename": filename,
                "slug": slug_name,
                "title": rule_title if agent_system == "claude" else skill_name
            }
            self.wfile.write(json.dumps(response_payload).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
