# Tweet2Skill Chrome Extension & Native Bridge

**Tweet2Skill** is a lightweight browser companion utility designed for developers using AI coding agents. It extracts content (such as documentation, code snippets, or full threads on X/Twitter) from your browser and parses it into structured **Skills** or **Rules** for agent environments.

## Supported Editor & Agent Systems
- **Google Antigravity:** Generates skill directories (`SKILL.md`) under `~/.gemini/config/skills/` or project-scoped `.agents/skills/`.
- **Claude Code:** Generates custom instruction rules under `~/.claude/rules/` or project-scoped `.claude/rules/`.
- **Cursor:** Generates cursor rules under `~/.cursor/rules/` or project-scoped `.cursor/rules/` (Pro/BYOK).
- **Windsurf:** Appends rules to `~/.windsurfrules` or project-scoped `.windsurfrules` (Pro/BYOK).
- **GitHub Copilot:** Appends instructions to `~/.github/copilot-instructions.md` or project-scoped `.github/copilot-instructions.md` (Pro/BYOK).

---

## Features
- **Smart DOM Extraction:** Highlight a specific code snippet or paragraph, or click to auto-extract full threads from X (Twitter) status pages.
- **Dual connection modes:**
  - **Local Host:** Uses a native messaging Python script (`save_skill.py`) to write generated rules directly into your computer's editor folders silently.
  - **Cloud Mode:** Generates and triggers browser downloads directly when the native host bridge is not running.
- **Bring Your Own Key (BYOK):** Set your own Gemini API Key locally in the extension settings to run unlimited generations directly through the Gemini API.

---

## Installation & Setup

### 1. Load the Chrome Extension
1. Download this repository as a ZIP archive and extract it (or clone it).
2. Open Google Chrome and navigate to `chrome://extensions/`.
3. Toggle on **Developer mode** in the top-right corner.
4. Click the **Load unpacked** button in the top-left corner and select this directory.
5. Copy the generated **Extension ID** from the extension card — you'll need it to set up the Native Host bridge.

### 2. Set Up the Native Host Bridge (Optional, for Local Saving)
The local native messaging host allows the extension to write files directly to your hard drive.
1. Open your terminal inside this project directory.
2. Run the helper installation script:
   ```bash
   python3 install.py
   ```
3. When prompted, paste the **Extension ID** you copied from Chrome.
4. Open the extension popup, go to **Settings**, choose **Local Host**, configure your **Workspace Path**, and save.

---

## Customizing and Modifying
As an open-source project, developers can modify, extend, or run their own instances:
- **API Key & Limits:** The default proxy handles up to 10 generations per day. To remove all limits locally, simply paste your own Gemini API key under **Settings > Bring Your Own Key (BYOK)**.
- **Custom Prompts:** You can modify the prompts or agent configurations inside `popup.js` and `save_skill.py`.
- **Add New Editor Formats:** Extend the systems array inside `popup.js` and target file path mappings inside `save_skill.py` to support other editors like Zed, VS Code, or Vim.

---

## Privacy & Security
All Gemini API keys, workspace paths, and authorization tokens are stored locally inside Chrome's secure `chrome.storage.local` store. No credentials ever touch third-party servers.
