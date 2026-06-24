<p align="center">
  <img src="icons/icon.svg" width="96" height="96" alt="Tweet2Skill Logo"/>
</p>

<h1 align="center">Tweet2Skill 🚀</h1>

<p align="center">
  <strong>Convert X/Twitter tweets, threads, or web pages into Google Antigravity Agent Skills & Claude Rules with one click.</strong>
</p>

<p align="center">
  <a href="https://tweet2skill.hero-apps.com"><strong>🌐 Live Website</strong></a> • 
  <a href="https://x.com/DorienVibecodes"><strong>🐦 Connect on X (Twitter)</strong></a>
</p>

---

## Features

- **Smart DOM Extraction:**
  - **Highlight Mode:** Convert only your selected/highlighted text.
  - **Thread Mode:** Extract full X/Twitter detail pages (automatically combines tweets by the same author in a thread).
  - **Page Mode:** Extracts clean, metadata-stripped body text from general web pages.
- **Interactive UI:** A beautiful dark-theme glassmorphism Chrome popup UI built using modern design standards.
- **Zero-Dependency Native Host:** Python messaging host uses built-in `urllib` to contact Gemini API. No `pip install` required.
- **Environment Aware:** Shell wrapper ensures `pyenv` and user environment variables load correctly.
- **Scope & System Options:**
  - **Google Antigravity:** Saves skills to `~/.gemini/config/skills/` (Global) or `.agents/skills/` (Workspace) formatted with YAML frontmatter.
  - **Claude Code:** Saves rules to `~/.claude/rules/` (Global) or `.claude/rules/` (Workspace) formatted as standard markdown.

---

## Installation & Setup

### Step 1: Load the Chrome Extension
1. Open Google Chrome and go to `chrome://extensions/`.
2. Enable **Developer mode** using the toggle in the top-right corner.
3. Click **Load unpacked** (top-left button).
4. Select this project directory (`/Users/dorienvandenabbeele/TweetSkill/`).
5. Copy the generated **Extension ID** (e.g. `cbmghhnbpdfehmkifhlbckcphclmbifn`).

### Step 2: Choose Your Connection Mode

#### Option A: Cloud Mode (Vercel) — Zero Local Setup!
1. **Deploy to Vercel:** Click the Vercel deploy button or run `vercel` in this directory to deploy the python serverless backend (`api/generate.py`).
2. Copy your deployed Vercel URL (e.g. `https://tweet2skill.vercel.app`).
3. Open the extension popup, go to **Settings**, select **Cloud Vercel**, paste your **Vercel Endpoint URL** and **Gemini API Key**, and click **Save Settings**.
*Your generations will be fetched via the Vercel API and downloaded directly to your browser download folder, prompting you where to save.*

#### Option B: Local Host Mode — Silent Background Saving (No Popups)
1. Open your terminal in this directory.
2. Register the local native host by running:
   ```bash
   python3 install.py
   ```
3. When prompted, paste the **Extension ID** you copied.
4. Open the extension popup, go to **Settings**, select **Local Host**, enter your **Gemini API Key** and **Local Workspace Path**, and click **Save Settings**.
*Your generations are written silently directly to your global or workspace directories.*

---

## How to Use

1. Go to any page (e.g. an X/Twitter post containing prompt instructions, a GitHub Readme, or a Codelab).
2. Open the extension popup.
3. Choose the target **Agent System**:
   - **Antigravity:** Formats as a Custom Agent Skill with YAML frontmatter.
   - **Claude Code:** Formats as a clean markdown Rule (`CLAUDE.md` rule format).
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

## How to Package and Distribute (Gumroad / Lemon Squeezy / Web Store)

If you want to package this to sell or share with other developers:

### Option A: Packaged Local Download (For Developers)
1. **Compile the Python Host:**
   To remove the requirement for python on user systems, compile `save_skill.py` into a binary:
   ```bash
   pip install pyinstaller
   pyinstaller --onefile save_skill.py
   ```
2. **Automate Host Registry:**
   Update `install.py` to compile as an installer (.dmg / .exe) that writes the `com.antigravity.linker.json` file automatically into the OS default folder:
   - **macOS:** `~/Library/Application Support/Google/Chrome/NativeMessagingHosts/`
   - **Windows:** Registry key at `HKEY_CURRENT_USER\Software\Google\Chrome\NativeMessagingHosts\com.antigravity.linker`
3. **Publish Extension:**
   Zip the extension folder (excluding python/shell scripts and `host.log`) and upload it to the **Chrome Web Store Developer Dashboard** ($5 fee). Specify that it uses `nativeMessaging` in your review justifications.
4. **Digital storefront:** Use Gumroad or Lemon Squeezy to deliver the executable/installer bundle.

### Option B: Cloud-Based SaaS Model (Easiest & Most Premium)
Instead of local native messaging (which requires a local script running on the user's OS):
1. **Build a Backend API:**
   Deploy `save_skill.py` as an API route on a cloud server (Vercel, Render, or Supabase).
2. **Update Popup Javascript:**
   Instead of `chrome.runtime.sendNativeMessage`, make a standard `fetch()` post request to your backend API containing the scraped content.
3. **Download File directly:**
   The backend API returns the formatted `SKILL.md` markdown text, and the extension popup displays a button to copy it or triggers a file download:
   ```js
   // Chrome Extension download logic:
   chrome.downloads.download({
     url: 'data:text/markdown;charset=utf-8,' + encodeURIComponent(markdownText),
     filename: 'SKILL.md',
     saveAs: true
   });
   ```
4. **Subscription SaaS:** Sell a premium subscription using Stripe Billing to cover your Gemini API cost.
