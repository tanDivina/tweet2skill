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

def clean_markdown(text):
    """Strip code block wrappers if the model wrapped its output in fences."""
    text = text.strip()
    # Strip opening ```markdown or ```
    text = re.sub(r"^```markdown\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    # Strip closing ```
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

def process_request(msg):
    """Processes the message payload from the extension."""
    url = msg.get("url", "")
    title = msg.get("title", "")
    content = msg.get("content", "")
    api_key = msg.get("apiKey", "")
    scope = msg.get("scope", "global")
    workspace_path = msg.get("workspacePath", "")
    agent_system = msg.get("agentSystem", "antigravity")

    if not api_key:
        return {"status": "error", "message": "API key missing in host payload."}
    
    if not content:
        return {"status": "error", "message": "No content was extracted to convert."}

    log(f"Processing content from {url} (System: {agent_system}, Scope: {scope})")
    
    try:
        # Call Gemini API to generate the skill or rule
        generated_content = call_gemini_api(api_key, content, url, agent_system)
        generated_content = clean_markdown(generated_content)
        
        if agent_system == "claude":
            # Extract rule title from first line starting with #
            title_match = re.search(r"^#\s*([^\n]+)", generated_content, re.MULTILINE)
            if title_match:
                rule_title = title_match.group(1).strip()
                log(f"Extracted rule title from generated markdown: {rule_title}")
            else:
                rule_title = title or "custom-rule"
                log(f"Could not extract rule title. Defaulting to: {rule_title}")

            slug_name = slugify(rule_title) or "custom-rule"
            
            # Determine target directory
            if scope == "global":
                # Saves to ~/.claude/rules/
                target_dir = os.path.expanduser("~/.claude/rules")
            else:
                # Saves to workspacePath/.claude/rules/
                if not workspace_path:
                    workspace_path = SCRIPT_DIR
                target_dir = os.path.join(workspace_path, ".claude", "rules")
                
            os.makedirs(target_dir, exist_ok=True)
            file_path = os.path.join(target_dir, f"{slug_name}.md")
            
            log(f"Writing Claude Code rule to {file_path}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(generated_content)
                
            friendly_path = file_path.replace(os.path.expanduser("~"), "~")
            return {
                "status": "done",
                "message": f"Successfully created Claude rule '{rule_title}'!\nSaved to: {friendly_path}"
            }
            
        else: # antigravity
            # Parse the YAML frontmatter to retrieve the skill name
            name_match = re.search(r"^name:\s*([^\n]+)", generated_content, re.MULTILINE)
            if name_match:
                skill_name = name_match.group(1).strip().strip('"').strip("'")
                log(f"Extracted skill name from generated frontmatter: {skill_name}")
            else:
                skill_name = slugify(title) or "extracted-skill"
                log(f"Could not extract skill name. Defaulting to slugified title: {skill_name}")

            slug_name = slugify(skill_name) or "custom-skill"

            # Determine target directory
            if scope == "global":
                # Saves to ~/.gemini/config/skills/
                base_dir = os.path.expanduser("~/.gemini/config")
                target_dir = os.path.join(base_dir, "skills", slug_name)
            else:
                # Saves to workspacePath/.agents/skills/
                if not workspace_path:
                    workspace_path = SCRIPT_DIR
                target_dir = os.path.join(workspace_path, ".agents", "skills", slug_name)

            os.makedirs(target_dir, exist_ok=True)
            file_path = os.path.join(target_dir, "SKILL.md")

            log(f"Writing SKILL.md to {file_path}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(generated_content)

            friendly_path = file_path.replace(os.path.expanduser("~"), "~")
            return {
                "status": "done",
                "message": f"Successfully created skill '{skill_name}'!\nSaved to: {friendly_path}"
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
