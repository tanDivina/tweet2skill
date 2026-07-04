<p align="center">
  <img src="icons/icon.svg" width="96" height="96" alt="Tweet2Skill Logo"/>
</p>

<h1 align="center">Tweet2Skill</h1>

<p align="center">
  <strong>Convert X/Twitter tweets, threads, or web pages into Google Antigravity Agent Skills & Claude Rules with one click.</strong>
</p>

<p align="center">
  <a href="https://tweet2skill.hero-apps.com"><strong>🌐 Live Website</strong></a> • 
  <a href="https://x.com/DorienVibecodes"><strong>🐦 Connect on X (Twitter)</strong></a>
</p>

---

## Supported Agent Systems

Tweet2Skill formats and matches the specific directory conventions, file structures, and naming requirements of the following systems:

1. **Google Antigravity:** Generates skills under `~/.gemini/config/skills/` (Global) or project-scoped `.agents/skills/` formatted with standard YAML frontmatter attributes.
2. **Claude Code:** Generates custom markdown rule logs under `~/.claude/rules/` (Global) or project-scoped `.claude/rules/` formatted in standard markdown.
3. **Cursor:** Generates settings file rules under `~/.cursor/rules/` (Global) or project-scoped `.cursor/rules/`.
4. **Windsurf:** Appends rule configurations to `~/.windsurfrules` (Global) or project-scoped `.windsurfrules`.
5. **GitHub Copilot:** Appends custom prompt instructions to `~/.github/copilot-instructions.md` (Global or Workspace).

---

## Features

- **Smart DOM Extraction:**
  - **Highlight Mode:** Convert only your selected/highlighted text.
  - **Thread Mode:** Extract full X/Twitter detail pages (automatically combines tweets by the same author in a thread).
  - **Page Mode:** Extracts clean, metadata-stripped body text from general web pages.
- **Interactive UI:** A beautiful dark-theme glassmorphism Chrome popup UI built using modern design standards.
- **Zero-Dependency Native Host:** Python messaging host uses built-in `urllib` to contact Gemini API. No `pip install` required.
- **Environment Aware:** Shell wrapper ensures `pyenv` and user environment variables load correctly.

---

## Installation & Setup

### Step 1: Load the Chrome Extension
1. Open Google Chrome and go to `chrome://extensions/`.
2. Enable **Developer mode** using the toggle in the top-right corner.
3. Click **Load unpacked** (top-left button).
4. Select this project directory.
5. Copy the generated **Extension ID** (e.g. `cbmghhnbpdfehmkifhlbckcphclmbifn`).

### Step 2: Choose Your Connection Mode

#### Option A: Cloud Mode — Zero Local Setup!
This mode uses a clean, web-based connection that prompts direct file downloads:
1. Open the extension popup, go to the **Settings** tab.
2. Under **Connection Mode**, select **Cloud Mode**.
3. (Optional) Under **Bring Your Own Key (BYOK)**, enter your custom Google Gemini API Key.
4. Set the API endpoint url to your backend server handler or proxy.
*Your generations will be processed and downloaded directly via your browser's download folder.*

#### Option B: Local Host Mode — Silent Background Saving
The local native messaging host allows the extension to write files directly to your local workspace folders silently:
1. Open your terminal in this project directory.
2. Register the local native host by running the setup installer:
   ```bash
   python3 install.py
   ```
3. When prompted, paste the **Extension ID** you copied from the extensions page.
4. Open the extension popup, go to **Settings**, select **Local Host**, enter your **Gemini API Key** and your target **Local Workspace Path**, and click **Save Settings**.
*Your generations are written silently directly to your global or workspace directories without browser download prompt dialogues.*

---

## How to Use

1. Go to any page (e.g. an X/Twitter post containing prompt instructions, a GitHub Readme, or a Codelab).
2. Open the extension popup.
3. Choose the target **Agent System** (Antigravity, Claude Code, Cursor, Windsurf, or GitHub Copilot).
4. Choose the target scope:
   - **Global:** Skill/Rule is instantly available across all your sessions.
   - **Workspace:** Skill/Rule is only loaded when working within the configured workspace.
5. Click **Turn into Skill** / **Turn into Rule**.
6. The Linker will automatically scrape, clean, and format the instructions using Gemini API, then save the final markdown file directly into your filesystem!

---

## Troubleshooting & Logs

Because Chrome runs Native Messaging hosts in the background, `print` statements are blocked (they crash the socket).
To debug or check status, inspect:
- **Host Logs:** Check the local file `host.log` in this folder.
- **Chrome Debugger:** Right-click the extension icon -> click **Inspect Popup** to see runtime Javascript errors.

---

## Custom Package Compilation (For Developers)

If you are modifying this tool for team distribution or custom pipelines:

### Option A: Compiling Python Native Host into a Binary
To package the Python bridge for environments without native Python runtimes, compile `save_skill.py` into a portable binary:
```bash
pip install pyinstaller
pyinstaller --onefile save_skill.py
```

### Option B: Deploying a Custom Serverless API
You can run the parsing logic as a serverless endpoint by hosting the generator module on Vercel, Render, or a custom VPS:
1. Extract the Python parsing logic into a serverless HTTP endpoint.
2. Send scraped DOM data via a standard POST request from the extension.
3. Return the formatted markdown text and prompt a download directly in the user browser using:
   ```js
   chrome.downloads.download({
     url: 'data:text/markdown;charset=utf-8,' + encodeURIComponent(markdownText),
     filename: 'SKILL.md',
     saveAs: true
   });
   ```

---

## ⚡ Non-Developers: Quick Start & Store Installation

If you are a user looking to install the **official, pre-packaged version** of Tweet2Skill without manually running terminal installation commands, loading unpacked folders, or managing python local scripts:

1. **Install from the Web Store:** Visit the official **[Chrome Web Store Page](https://chrome.google.com/webstore/detail/cbmghhnbpdfehmkifhlbckcphclmbifn)** and click **Add to Chrome**.
2. **Visit our Website:** Check out **[https://tweet2skill.hero-apps.com](https://tweet2skill.hero-apps.com)** to learn more about the tool and explore pricing plans.
3. **Instant Setup:** The Web Store version is configured to run automatically out-of-the-box in **Cloud Mode** with zero local setup requirements!

---

## License & Usage

This software is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)** license. 

*   **Allowed:** Developers are free to inspect the source code, fork the repository, modify the logic, and run local unpacked versions of this extension for personal, non-commercial use.
*   **Prohibited:** You **cannot** package this software, host its services, or redistribute its components for commercial advantage, retail sales, or monetary compensation under any circumstances.


