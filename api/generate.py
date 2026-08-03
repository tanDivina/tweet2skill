"""
/api/generate – Main skill/rule generation endpoint.

Supports three tiers:
  - free:  Uses server-side GEMINI_API_KEY, 3/day AND 10/week limits, no signup needed
  - byok:  Uses user's own API key, proxied through server, 3/min burst only
  - pro:   Uses server-side key, consumable credits (2,500 credits), no daily limits

Backward-compatible: requests with apiKey in body and no auth headers → BYOK.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import re
import sys
import urllib.request
import urllib.error

# ── Shared library imports ──────────────────────────────────────────
from api._lib import auth_utils, rate_limiter, tier as tier_mod, upstash


# ── Agent system prompts ────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "antigravity": (
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
    ),
    "claude": (
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
    ),
    "cursor": (
        "You are a Cursor Rules generator. Take the provided web or tweet content "
        "and convert it into a structured Cursor rules file.\n\n"
        "The output must exactly follow this format:\n"
        "# [Rule Title]\n\n"
        "[Brief description of what this rule covers and when it applies.]\n\n"
        "## Rules\n\n"
        "[Convert the core guidelines, coding patterns, or rules into precise, numbered, "
        "action-oriented instructions for the Cursor AI coding assistant.]\n\n"
        "## Examples\n\n"
        "[If applicable, include 1-2 short code examples showing correct vs incorrect patterns.]\n\n"
        "CRITICAL RULES:\n"
        "1. DO NOT include any YAML frontmatter or triple-dashes (---).\n"
        "2. DO NOT wrap the output in ```markdown or ``` block code fences.\n"
        "3. Do not add any conversational text before or after the markdown block.\n"
        "4. Focus on actionable, specific instructions that Cursor can follow."
    ),
    "windsurf": (
        "You are a Windsurf Rules generator. Take the provided web or tweet content "
        "and convert it into structured Windsurf rules.\n\n"
        "The output must exactly follow this format:\n"
        "# [Rule Title]\n\n"
        "[Brief trigger description: when should Windsurf apply these rules?]\n\n"
        "## Guidelines\n\n"
        "[Convert the core rules and patterns into clear, numbered guidelines for the "
        "Windsurf AI coding assistant. Be specific and actionable.]\n\n"
        "## Constraints\n\n"
        "[List any important constraints, anti-patterns to avoid, or boundary conditions.]\n\n"
        "CRITICAL RULES:\n"
        "1. DO NOT include any YAML frontmatter or triple-dashes (---).\n"
        "2. DO NOT wrap the output in ```markdown or ``` block code fences.\n"
        "3. Do not add any conversational text before or after the markdown block.\n"
        "4. Write in imperative mood – tell Windsurf what to DO."
    ),
    "copilot": (
        "You are a GitHub Copilot Instructions generator. Take the provided web or tweet content "
        "and convert it into a copilot-instructions.md file.\n\n"
        "The output must exactly follow this format:\n"
        "# [Title]\n\n"
        "[One-line summary of what these instructions cover.]\n\n"
        "## Instructions\n\n"
        "[Convert the core rules, patterns, and guidelines into clear, numbered instructions "
        "for GitHub Copilot. Focus on coding conventions, preferred patterns, and project-specific rules.]\n\n"
        "## Preferred Patterns\n\n"
        "[List preferred code patterns, naming conventions, or architectural decisions.]\n\n"
        "CRITICAL RULES:\n"
        "1. DO NOT include any YAML frontmatter or triple-dashes (---).\n"
        "2. DO NOT wrap the output in ```markdown or ``` block code fences.\n"
        "3. Do not add any conversational text before or after the markdown block.\n"
        "4. Keep instructions specific enough for Copilot to act on directly."
    ),
}

CLAUDE_SKILL_PROMPT = (
    "You are a Claude Code Skill generator. Take the provided web or tweet content "
    "and convert it into a structured Markdown block representing a Claude Code agent skill.\n\n"
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

# Enhanced system prompt suffix for Pro tier
PRO_ENHANCEMENT = (
    "\n\nADDITIONAL PRO ENHANCEMENTS:\n"
    "- Provide deeper, more detailed instructions with edge-case handling.\n"
    "- Include a '## Advanced Notes' section with nuanced best practices.\n"
    "- Where applicable, add context on WHY each rule matters.\n"
    "- Aim for comprehensive, production-grade output."
)

# Filename patterns per agent system
FILENAME_MAP = {
    "antigravity": "SKILL.md",
    "claude": "{slug}.md",
    "cursor": ".cursorrules",
    "windsurf": ".windsurfrules",
    "copilot": "copilot-instructions.md",
}


# ── Helpers ─────────────────────────────────────────────────────────

def slugify(text):
    """Convert text into a clean folder name slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\-]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def call_gemini_api(api_key, content, source_url, agent_system="antigravity", is_pro=False, agent_format="rule"):
    """Send text to the Gemini API and return the generated markdown."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    if agent_system == "claude" and agent_format == "skill":
        system_prompt = CLAUDE_SKILL_PROMPT
    else:
        system_prompt = SYSTEM_PROMPTS.get(agent_system, SYSTEM_PROMPTS["antigravity"])

    if is_pro:
        system_prompt += PRO_ENHANCEMENT

    user_prompt = f"Source URL: {source_url}\n\nRaw Content:\n{content}"

    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"temperature": 0.2},
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
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


def clean_markdown(text):
    """Strip code block wrappers if the model wrapped its output in fences."""
    text = text.strip()
    text = re.sub(r"^```markdown\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def json_error(handler, status_code, message):
    """Send a JSON error response with CORS headers."""
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(
        json.dumps({"status": "error", "message": message}).encode("utf-8")
    )


def json_response(handler, status_code, data):
    """Send a JSON response with CORS headers."""
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode("utf-8"))


def extract_title_and_slug(generated_content, agent_system, fallback_title, agent_format="rule"):
    """Extract title and slug from generated content based on agent system."""
    if agent_system == "antigravity" or (agent_system == "claude" and agent_format == "skill"):
        name_match = re.search(r"^name:\s*([^\n]+)", generated_content, re.MULTILINE)
        skill_name = (
            name_match.group(1).strip().strip("\"'") if name_match
            else (slugify(fallback_title) or "custom-skill")
        )
        slug = slugify(skill_name) or "custom-skill"
        filename = "SKILL.md"
        title = skill_name
    else:
        title_match = re.search(r"^#\s*([^\n]+)", generated_content, re.MULTILINE)
        title = (
            title_match.group(1).strip() if title_match
            else (fallback_title or "custom-rule")
        )
        slug = slugify(title) or "custom-rule"

        tmpl = FILENAME_MAP.get(agent_system, "{slug}.md")
        filename = tmpl.replace("{slug}", slug)

    return title, slug, filename


# ── Request handler ─────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, X-Device-Id, X-Request-Signature",
        )
        self.end_headers()

    def do_POST(self):
        # ── 0. Read body ────────────────────────────────────────────
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)

        try:
            payload = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            json_error(self, 400, "Malformed JSON payload.")
            return

        # ── 1. Origin validation ────────────────────────────────────
        if not auth_utils.validate_origin(self):
            json_error(self, 403, "Forbidden: invalid request origin.")
            return

        # ── 2. Extract fields ───────────────────────────────────────
        url = payload.get("url", "")
        title = payload.get("title", "")
        content = payload.get("content", "")
        agent_system = payload.get("agentSystem", "antigravity")
        agent_format = payload.get("agentFormat", "rule")
        export_agents = payload.get("exportAgents", None)  # Pro multi-agent

        if not content:
            json_error(self, 400, "Content to process is empty.")
            return

        # ── 3. Detect tier ──────────────────────────────────────────
        tier_info = tier_mod.detect_tier(self, payload)
        current_tier = tier_info["tier"]
        client_ip = auth_utils.get_client_ip(self)

        # ── 4. Determine the Gemini API key to use ──────────────────
        if current_tier == "byok":
            api_key = tier_info["apiKey"]
            if not api_key:
                json_error(self, 400, "API key missing in request.")
                return
        else:
            # Free & Pro use the server-side key
            api_key = os.environ.get("GEMINI_API_KEY", "")
            if not api_key:
                json_error(self, 500, "Server API key not configured.")
                return

        # ── 5. Rate limiting ────────────────────────────────────────
        try:
            # 5a. Burst limit – ALL tiers (3/min)
            burst_id = tier_info["userId"] or tier_info["deviceId"] or client_ip
            burst = rate_limiter.check_burst(burst_id)
            if not burst["allowed"]:
                json_error(self, 429, "Rate limit exceeded. Please wait a moment.")
                return

            if current_tier == "free":
                device_id = tier_info["deviceId"]
                if device_id:
                    # 5b. Daily limit per deviceId (3/day)
                    daily_device = rate_limiter.check_daily(f"dev:{device_id}", 3)
                    if not daily_device["allowed"]:
                        json_error(
                            self, 429,
                            f"Daily free limit reached ({daily_device['limit']} generations/day). "
                            "Add your own API key or buy credits."
                        )
                        return

                    # 5c. Weekly limit per deviceId (10/week)
                    weekly_device = rate_limiter.check_weekly(f"dev:{device_id}", 10)
                    if not weekly_device["allowed"]:
                        json_error(
                            self, 429,
                            f"Weekly free limit reached ({weekly_device['limit']} generations/week). "
                            "Add your own API key or buy credits."
                        )
                        return
                else:
                    # Fallback to IP-only checks
                    # 5d. Daily limit per IP (3/day)
                    daily_ip = rate_limiter.check_daily(f"ip:{client_ip}", 3)
                    if not daily_ip["allowed"]:
                        json_error(
                            self, 429,
                            f"Daily free limit reached for this network ({daily_ip['limit']}/day). "
                            "Add your own API key or buy credits."
                        )
                        return

                    # 5e. Weekly limit per IP (10/week)
                    weekly_ip = rate_limiter.check_weekly(f"ip:{client_ip}", 10)
                    if not weekly_ip["allowed"]:
                        json_error(
                            self, 429,
                            f"Weekly free limit reached for this network ({weekly_ip['limit']}/week). "
                            "Add your own API key or buy credits."
                        )
                        return

            elif current_tier == "pro":
                user_id = tier_info["userId"]
                email = tier_info.get("email", "")
                user_data = upstash.hgetall(f"user:{user_id}")
                sub_status = user_data.get("subscription", "")
                
                is_legacy_sub = (sub_status == "active" or email == "dorien.vda@gmail.com")
                credits_val = 0
                try:
                    credits_val = int(user_data.get("credits", "0"))
                except ValueError:
                    pass

                if is_legacy_sub:
                    # 5f. Monthly limit for Pro legacy sub
                    monthly = rate_limiter.check_monthly(user_id, 1250)
                    if not monthly["allowed"]:
                        json_error(
                            self, 429,
                            f"Monthly Pro limit reached ({monthly['limit']} skills/month). "
                            "Resets next month."
                        )
                        return
                elif credits_val > 0:
                    # Deduct credit before API call, refund if Gemini API fails
                    new_credits = upstash.hincrby(f"user:{user_id}", "credits", -1)
                    if new_credits < 0:
                        # Refund and block
                        upstash.hincrby(f"user:{user_id}", "credits", 1)
                        json_error(
                            self, 403,
                            "No credits remaining. Please buy more credits in settings."
                        )
                        return
                    deducted_credit = True
                else:
                    json_error(
                        self, 403,
                        "No credits remaining. Please buy more credits or insert your own API Key."
                    )
                    return

            # BYOK: no daily/monthly limits (only burst)

        except RuntimeError as e:
            # Redis unavailable – log but don't block (degrade gracefully)
            print(f"[rate-limiter] Redis error (allowing request): {e}", file=sys.stderr)

        # ── 6. Multi-agent export (Pro only) ────────────────────────
        if export_agents and current_tier == "pro":
            agents_to_generate = export_agents if isinstance(export_agents, list) else [agent_system]
        else:
            agents_to_generate = [agent_system]

        # Validate agent names
        agents_to_generate = [a for a in agents_to_generate if a in SYSTEM_PROMPTS]
        if not agents_to_generate:
            agents_to_generate = ["antigravity"]

        # ── 7. Generate content ─────────────────────────────────────
        try:
            is_pro = current_tier == "pro"
            results = {}

            for agent in agents_to_generate:
                generated = call_gemini_api(api_key, content, url, agent, is_pro, agent_format=agent_format)
                generated = clean_markdown(generated)
                agent_title, agent_slug, agent_filename = extract_title_and_slug(
                    generated, agent, title, agent_format=agent_format
                )
                results[agent] = {
                    "markdown": generated,
                    "filename": agent_filename,
                    "slug": agent_slug,
                    "title": agent_title,
                }

            # ── 8. Build response ───────────────────────────────────
            # For single-agent (or backward-compat), return flat response
            if len(results) == 1:
                agent_key = list(results.keys())[0]
                r = results[agent_key]
                response_payload = {
                    "status": "done",
                    "markdown": r["markdown"],
                    "filename": r["filename"],
                    "slug": r["slug"],
                    "title": r["title"],
                    "tier": current_tier,
                }
            else:
                # Multi-agent response
                response_payload = {
                    "status": "done",
                    "tier": current_tier,
                    "agents": results,
                    # Also include the primary agent as top-level for backward compat
                    "markdown": results.get(agent_system, list(results.values())[0])["markdown"],
                    "filename": results.get(agent_system, list(results.values())[0])["filename"],
                    "slug": results.get(agent_system, list(results.values())[0])["slug"],
                    "title": results.get(agent_system, list(results.values())[0])["title"],
                }

            json_response(self, 200, response_payload)

        except Exception as e:
            if current_tier == "pro" and 'deducted_credit' in locals() and deducted_credit:
                try:
                    upstash.hincrby(f"user:{tier_info['userId']}", "credits", 1)
                except Exception as refund_err:
                    print(f"[generate] Failed to refund credit: {refund_err}", file=sys.stderr)
            json_error(self, 500, str(e))
