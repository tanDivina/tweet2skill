#!/usr/bin/env python3
import sys
import json
import struct
import os
import re
import urllib.request
import urllib.error

# Setup logging to a local file in the same folder as the script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "host.log")

# Proxy API base URL
PROXY_API_BASE = "https://tweet2skill.hero-apps.com"

def log(message):
    """Write log messages to a local file to avoid cluttering stdout."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
    except Exception:
        pass

def read_message():
    """Reads a message from Chrome via standard input."""
    try:
        # Read the first 4 bytes representing message length
        text_length_bytes = sys.stdin.buffer.read(4)
        if not text_length_bytes:
            log("No length bytes received, exiting.")
            sys.exit(0)
        
        # Unpack length (little-endian 32-bit integer)
        text_length = struct.unpack('I', text_length_bytes)[0]
        log(f"Received message length: {text_length}")
        
        # Read the message bytes
        text_data = sys.stdin.buffer.read(text_length).decode('utf-8')
        return json.loads(text_data)
    except Exception as e:
        log(f"Error reading message: {str(e)}")
        sys.exit(1)

def send_message(message):
    """Sends a response back to Chrome via standard output."""
    try:
        text_data = json.dumps(message).encode('utf-8')
        # Write 4-byte length prefix
        sys.stdout.buffer.write(struct.pack('I', len(text_data)))
        # Write message contents
        sys.stdout.buffer.write(text_data)
        sys.stdout.buffer.flush()
        log(f"Successfully sent response: {message.get('status')}")
    except Exception as e:
        log(f"Error sending message: {str(e)}")

def slugify(text):
    """Convert text into a clean folder name slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\-]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def call_gemini_api(api_key, content, source_url, agent_system="antigravity"):
    """Send text to the Gemini API directly using the user's own key (BYOK mode)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    system_prompt = get_system_prompt(agent_system)
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

    log(f"Calling Gemini API at {url.split('?')[0]}")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
            # Extract text response from Gemini structure
            candidates = res_data.get("candidates", [])
            if not candidates:
                raise ValueError("No API response candidates returned.")
            
            text = candidates[0].get("content", {}).get("parts", [])[0].get("text", "")
            return text
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        log(f"Gemini API HTTP Error {e.code}: {error_body}")
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("error", {}).get("message", "HTTP Error")
            raise Exception(f"Gemini API Error: {msg}")
        except json.JSONDecodeError:
            raise Exception(f"Gemini API returned status {e.code}: {e.reason}")
    except Exception as e:
        log(f"Request Exception: {str(e)}")
        raise e

def call_proxy_api(content, source_url, agent_system, device_id, auth_token=None, api_key=None):
    """Route the generation request through the Tweet2Skill proxy API."""
    endpoint = f"{PROXY_API_BASE}/api/generate"
    
    payload = {
        "url": source_url,
        "content": content,
        "agentSystem": agent_system
    }
    
    # Include API key if BYOK
    if api_key:
        payload["apiKey"] = api_key

    headers = {
        "Content-Type": "application/json",
        "X-Device-Id": device_id or "local-host"
    }
    
    # Include JWT auth token if available (Pro users)
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=req_data,
        headers=headers,
        method="POST"
    )

    log(f"Calling proxy API at {endpoint}")
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
            if res_data.get("status") == "done" and res_data.get("markdown"):
                return res_data["markdown"]
            else:
                raise Exception(res_data.get("message", "Unknown proxy API error"))
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        log(f"Proxy API HTTP Error {e.code}: {error_body}")
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("message", f"HTTP {e.code}")
            if e.code == 429:
                raise Exception(f"Daily limit reached. Upgrade to Pro ($19/yr) or use your own API key.")
            raise Exception(f"Proxy API Error: {msg}")
        except json.JSONDecodeError:
            raise Exception(f"Proxy API returned status {e.code}")
    except Exception as e:
        log(f"Proxy Request Exception: {str(e)}")
        raise e

def get_system_prompt(agent_system):
    """Get the appropriate system prompt for the given agent system."""
    if agent_system == "claude":
        return (
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
    elif agent_system == "cursor":
        return (
            "You are a Cursor IDE rule generator. Take the provided web or tweet content "
            "and convert it into a structured Markdown block representing a Cursor development rule.\n\n"
            "The output must exactly follow this format:\n"
            "# [Rule Title]\n\n"
            "[Brief description of what this rule enforces and when Cursor should apply it.]\n\n"
            "## Rules\n"
            "[Convert the core guidelines into precise, clean, action-oriented rules that Cursor's AI will follow when writing and reviewing code.]\n\n"
            "CRITICAL RULES:\n"
            "1. DO NOT include any YAML frontmatter or triple-dashes (---).\n"
            "2. DO NOT wrap the output in ```markdown or ``` block code fences.\n"
            "3. Do not add any conversational text before or after the markdown block."
        )
    elif agent_system == "windsurf":
        return (
            "You are a Windsurf IDE rule generator. Take the provided web or tweet content "
            "and convert it into a structured rules block for Windsurf's AI assistant.\n\n"
            "The output must exactly follow this format:\n"
            "# [Rule Title]\n\n"
            "[Brief description of what this rule covers.]\n\n"
            "## Guidelines\n"
            "[Convert the core rules, coding patterns, or best practices into precise, clean instructions that Windsurf's Cascade AI will follow.]\n\n"
            "CRITICAL RULES:\n"
            "1. DO NOT include any YAML frontmatter or triple-dashes (---).\n"
            "2. DO NOT wrap the output in ```markdown or ``` block code fences.\n"
            "3. Do not add any conversational text before or after the markdown block."
        )
    elif agent_system == "copilot":
        return (
            "You are a GitHub Copilot instructions generator. Take the provided web or tweet content "
            "and convert it into a structured instructions block for GitHub Copilot.\n\n"
            "The output must exactly follow this format:\n"
            "# [Instruction Title]\n\n"
            "[Brief description of what these instructions cover.]\n\n"
            "## Instructions\n"
            "[Convert the core guidelines into precise coding instructions that GitHub Copilot will follow when generating code suggestions.]\n\n"
            "CRITICAL RULES:\n"
            "1. DO NOT include any YAML frontmatter or triple-dashes (---).\n"
            "2. DO NOT wrap the output in ```markdown or ``` block code fences.\n"
            "3. Do not add any conversational text before or after the markdown block."
        )
    else:  # antigravity (default)
        return (
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

def clean_markdown(text):
    """Strip code block wrappers if the model wrapped its output in fences."""
    text = text.strip()
    # Strip opening ```markdown or ```
    text = re.sub(r"^```markdown\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    # Strip closing ```
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

def get_file_path(agent_system, slug_name, scope, workspace_path):
    """Determine the target file path based on agent system and scope."""
    if agent_system == "antigravity":
        if scope == "global":
            base_dir = os.path.expanduser("~/.gemini/config")
            target_dir = os.path.join(base_dir, "skills", slug_name)
        else:
            if not workspace_path:
                workspace_path = SCRIPT_DIR
            target_dir = os.path.join(workspace_path, ".agents", "skills", slug_name)
        os.makedirs(target_dir, exist_ok=True)
        return os.path.join(target_dir, "SKILL.md"), False  # (path, is_append)

    elif agent_system == "claude":
        if scope == "global":
            target_dir = os.path.expanduser("~/.claude/rules")
        else:
            if not workspace_path:
                workspace_path = SCRIPT_DIR
            target_dir = os.path.join(workspace_path, ".claude", "rules")
        os.makedirs(target_dir, exist_ok=True)
        return os.path.join(target_dir, f"{slug_name}.md"), False

    elif agent_system == "cursor":
        if scope == "global":
            target_dir = os.path.expanduser("~/.cursor/rules")
        else:
            if not workspace_path:
                workspace_path = SCRIPT_DIR
            target_dir = os.path.join(workspace_path, ".cursor", "rules")
        os.makedirs(target_dir, exist_ok=True)
        return os.path.join(target_dir, f"{slug_name}.md"), False

    elif agent_system == "windsurf":
        if scope == "global":
            file_path = os.path.expanduser("~/.windsurfrules")
        else:
            if not workspace_path:
                workspace_path = SCRIPT_DIR
            file_path = os.path.join(workspace_path, ".windsurfrules")
        return file_path, True  # Append mode

    elif agent_system == "copilot":
        if scope == "global":
            target_dir = os.path.expanduser("~/.github")
        else:
            if not workspace_path:
                workspace_path = SCRIPT_DIR
            target_dir = os.path.join(workspace_path, ".github")
        os.makedirs(target_dir, exist_ok=True)
        return os.path.join(target_dir, "copilot-instructions.md"), True  # Append mode

    else:
        raise ValueError(f"Unknown agent system: {agent_system}")

def extract_title_and_slug(generated_content, agent_system, fallback_title):
    """Extract title and slug from generated content based on agent system."""
    if agent_system == "antigravity":
        name_match = re.search(r"^name:\s*([^\n]+)", generated_content, re.MULTILINE)
        if name_match:
            skill_name = name_match.group(1).strip().strip('"').strip("'")
        else:
            skill_name = slugify(fallback_title) or "extracted-skill"
        slug_name = slugify(skill_name) or "custom-skill"
        return skill_name, slug_name
    else:
        # For claude, cursor, windsurf, copilot — extract title from first # heading
        title_match = re.search(r"^#\s*([^\n]+)", generated_content, re.MULTILINE)
        if title_match:
            rule_title = title_match.group(1).strip()
        else:
            rule_title = fallback_title or "custom-rule"
        slug_name = slugify(rule_title) or "custom-rule"
        return rule_title, slug_name

def process_request(msg):
    """Processes the message payload from the extension."""
    url = msg.get("url", "")
    title = msg.get("title", "")
    content = msg.get("content", "")
    api_key = msg.get("apiKey", "")
    scope = msg.get("scope", "global")
    workspace_path = msg.get("workspacePath", "")
    agent_system = msg.get("agentSystem", "antigravity")
    device_id = msg.get("deviceId", "")
    auth_token = msg.get("authToken", "")

    if not content:
        return {"status": "error", "message": "No content was extracted to convert."}

    log(f"Processing content from {url} (System: {agent_system}, Scope: {scope})")
    
    try:
        # Determine generation method:
        # - If user has API key → can call Gemini directly OR go through proxy
        # - If no API key → must go through proxy (free/pro tier)
        if api_key:
            # BYOK mode: route through proxy for tracking
            log("BYOK mode: routing through proxy with user's API key")
            generated_content = call_proxy_api(content, url, agent_system, device_id, auth_token, api_key)
        else:
            # Free/Pro mode: route through proxy using server's API key
            log("Free/Pro mode: routing through proxy")
            generated_content = call_proxy_api(content, url, agent_system, device_id, auth_token)
        
        generated_content = clean_markdown(generated_content)
        
        # Extract title and slug
        display_name, slug_name = extract_title_and_slug(generated_content, agent_system, title)
        
        # Determine file path
        file_path, is_append = get_file_path(agent_system, slug_name, scope, workspace_path)
        
        # Write file
        if is_append:
            # For windsurf and copilot, append with a separator
            separator = "\n\n---\n\n"
            if os.path.exists(file_path):
                log(f"Appending to {file_path}")
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(separator + generated_content)
            else:
                log(f"Creating new file {file_path}")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(generated_content)
        else:
            log(f"Writing to {file_path}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(generated_content)

        friendly_path = file_path.replace(os.path.expanduser("~"), "~")
        
        # System-specific success message
        system_labels = {
            "antigravity": "skill",
            "claude": "rule",
            "cursor": "rule",
            "windsurf": "rule",
            "copilot": "instruction"
        }
        label = system_labels.get(agent_system, "skill")
        action = "Appended" if is_append else "Created"
        
        return {
            "status": "done",
            "message": f"Successfully {action.lower()} {agent_system.title()} {label} '{display_name}'!\nSaved to: {friendly_path}"
        }

    except Exception as e:
        log(f"Error during processing: {str(e)}")
        return {"status": "error", "message": str(e)}

def main():
    log("--- Antigravity Linker Host Started ---")
    while True:
        try:
            msg = read_message()
            response = process_request(msg)
            send_message(response)
        except KeyboardInterrupt:
            log("Host interrupted by keyboard.")
            break
        except SystemExit:
            log("System exit triggered.")
            break
        except Exception as e:
            log(f"Fatal error in main loop: {str(e)}")
            break

if __name__ == "__main__":
    main()
