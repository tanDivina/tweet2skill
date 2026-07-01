# Chrome Web Store Listing — Tweet2Skill

> Last Updated: 2026-07-01

This document contains the exact, updated copy-pasteable fields required to publish the **Tweet2Skill** Chrome Extension on the Google Chrome Web Store. It has been aligned with the latest 3-tier monetization model and permissions manifest.

---

## 1. Store Listing Details

### **Product Name** [Max 45 chars]
```text
Tweet2Skill
```

### **Short Description** [Max 150 chars]
```text
Convert X/Twitter threads, tweets, and webpages into Antigravity skills or Claude Code rules instantly.
```

### **Detailed Description** [Max 16,000 chars]
```text
Tweet2Skill is the ultimate companion tool for AI-assisted development and pair programming. With a single click, convert any educational tweet, high-value technical X/Twitter thread, or webpage into production-ready Antigravity (AGY) skills, Claude Code rules, or custom system prompts.

Stop struggling to copy-paste scattered advice across your browser tabs. Tweet2Skill parses tweets and website contents instantly, utilizes state-of-the-art AI parsing to generate clean developer skills, and saves them directly to your local workspace, Cursor configs, or Claude rules folders.

### Core Features:
* **Instant Conversions**: Convert X/Twitter threads or standard web pages into beautifully formatted markdown skills (.md files) instantly.
* **Workspace Syncing**: Saves files natively into your target workspace's custom agent skill folders.
* **Advanced Multi-System Support**: Choose from standard Antigravity structures, Claude Code configurations (.claudecoderc / CLAUDE.md), Cursor settings, Windsurf, or Copilot rules.
* **Flexible Connections**: Seamlessly switch between zero-config Local mode and secure Cloud Vercel routing.
* **Bring Your Own Key (BYOK)**: Use your own Google Gemini API key for unlimited free generation.

### Flexible Tier Structure:
1. **Free Anonymous Tier**: Get 3 generations per day (up to 10 per week) with zero signups or accounts required. Excellent for quick, casual use!
2. **Bring Your Own Key (BYOK)**: Connect your own Gemini API key for 100% free, unlimited, and high-performance generations.
3. **Pro Credits Pack**: A simple, one-time payment of $9.99 for 2,500 permanent cloud credits. No recurring subscriptions, no monthly commitments—just credits that never expire.

### How to use it:
1. Navigate to any educational X/Twitter thread or developer documentation page.
2. Click the Tweet2Skill extension icon in your toolbar.
3. Choose your target agent system (e.g., Antigravity, Claude Rules, Cursor, etc.).
4. Click "Generate Skill".
5. Your custom developer skill is parsed, saved, and ready to feed to your autonomous AI agents!

### Privacy & Security
Your API keys and workspace directories remain strictly saved inside your browser's local, secure, and encrypted storage. We do not sell or monetize your data.

---
Category: Developer Tools
```

---

## 2. Privacy & Single Purpose

### **Single Purpose Description** [Max 1,000 chars]
```text
Convert X/Twitter threads or developer webpages into custom agent skill markdown files (.md) for AI coding environments.
```

---

## 3. Permissions Justifications

Each permission requested in `manifest.json` must be justified for the Chrome Web Store review process. Copy and paste the exact text below for each permission in the developer console:

| Permission | Review Console Justification Text |
| :--- | :--- |
| **`activeTab`** | Required to read the URL and DOM content of the currently active tab to extract and parse tweets/webpages when the user explicitly clicks the extension action icon. |
| **`scripting`** | Required to execute a DOM parsing helper script on the active page to extract the full text and structure of educational X/Twitter threads and technical webpages. |
| **`nativeMessaging`** | Required to securely communicate with the local lightweight Python helper script (`save_skill.py`) to write the generated markdown skill files directly into the user's local workspace directories. |
| **`storage`** | Required to persist user preferences, connection settings (Local vs Cloud), chosen developer systems, and the user's custom Gemini API key (BYOK mode). |
| **`tabs`** | Required to access the active tab's metadata (URL and Title) during popup initialization to correctly pre-fill the workspace scope. |
| **`downloads`** | Used as a reliable fallback download mechanism to let users download skill files directly as browser downloads if they do not want to use the native python helper. |
| **`identity`** | Required to authenticate the user securely via Google OAuth to verify their email, associate their credit ledger, and track usage quotas. |

### Host Permissions

| Host Pattern | Justification Text |
| :--- | :--- |
| **`https://x.com/*`** | Allows the extension to run and extract text content from modern X.com posts and threads. |
| **`https://twitter.com/*`** | Allows backward compatibility and text extraction on twitter.com posts and threads. |
| **`https://tweet2skill.hero-apps.com/*`** | Allows secure communication with the product landing page for user authentication, Stripe integration, and documentation resources. |
| **`https://accounts.google.com/*`** | Required to securely perform Google OAuth token validation and secure sign-in. |

---

## 4. Data Usage & Consent Questionnaire

Answer the following questions in the Developer Dashboard exactly as shown below:

### 1. Data Collection
* **Does your extension collect or transmit user data?**
  * Select: **Yes**

### 2. Specific Data Categories Collected
* **Personal Communications (e.g., emails)**
  * **Collected**: Yes
  * **Off-device storage**: Yes
  * **Justification**: We collect the user's email address during secure Google Sign-In strictly to identify their account and associate their purchased credits (Pro pack) or track their free daily quotas.
* **Authentication Information**
  * **Collected**: Yes
  * **Off-device storage**: Yes
  * **Justification**: We process the Google ID Token to authenticate the user securely against our Vercel API and verify their identity before allowing credit-based generations.
* **Web History**
  * Select: **No** (The extension does not track history or send URLs off-device except for the specific page being actively parsed when the user clicks 'Generate Skill').
* **Location**
  * Select: **No**

### 3. Data Usage Certification
You must check the following checkboxes to certify your compliance with the CWS Developer Program Policy:
* [x] **No Selling**: I certify that I will not sell user data to third parties.
* [x] **No Unrelated Use**: I certify that I will not use user data for purposes unrelated to the extension's core functionality.
* [x] **No Credit Checks**: I certify that I will not use user data for creditworthiness or lending purposes.

---

## 5. Additional Developer Information

* **Privacy Policy URL**: `https://tweet2skill.hero-apps.com/privacy`
* **Homepage URL**: `https://tweet2skill.hero-apps.com`
* **Contact Email**: `support@hero-apps.com`
* **Visibility**: Public
