# Chrome Web Store Listing — Tweet2Skill

> Last Updated: 2026-06-25

## Store Listing

**Extension Name** [REQUIRED]
Tweet2Skill

**Short Description** [REQUIRED]
Convert X/Twitter tweets, threads, or web pages into Antigravity skills or Claude Code rules instantly.

**Detailed Description** [REQUIRED]
Tweet2Skill is the ultimate companion tool for AI-assisted development. With a single click, convert any educational tweet, high-value technical X/Twitter thread, or webpage into production-ready Antigravity (AGY) skills or Claude Code rules. 

Stop struggling to copy-paste scattered advice across your browser tabs. Tweet2Skill parses tweets and website contents instantly, utilizes state-of-the-art AI parsing to generate clean custom developer skills, and saves them directly to your local workspace, cursor configs, or Claude rules folders.

### Core Features:
* **Instant Conversions**: Convert X/Twitter threads or standard web pages into formatted markdown skills (.md files) instantly.
* **Workspace Syncing**: Saves files natively into your target workspace's custom agent skill folders.
* **Advanced Multi-System Support**: Choose from standard Antigravity structures, Claude Code configurations, Cursor settings, Windsurf, or Copilot rules.
* **Flexible Connections**: Seamlessly switch between zero-config Local mode and secure Cloud Vercel routing.
* **Bring Your Own Key (BYOK)**: Use your own Gemini API key for unlimited free usage, or access our curated cloud-limit tiers.

### How to use it:
1. Navigate to any educational X/Twitter thread or developer documentation page.
2. Click the Tweet2Skill extension icon.
3. Choose your target agent system (e.g., Antigravity or Claude Rules).
4. Click "Generate Skill".
5. Your custom developer skill is parsed, saved, and ready to feed to your autonomous AI agents!

### Privacy & Security
Your API keys and workspace directories remain strictly saved inside your browser's local, encrypted storage. We do not sell or monetize your data.

---

**Category** [REQUIRED]
Developer Tools

**Single Purpose** [REQUIRED]
Convert X/Twitter threads or developer webpages into custom agent skill markdown files (.md) for AI coding environments.

**Primary Language** [REQUIRED]
English

---

## Graphics & Assets

| Asset | Dimensions | Status | Filename |
|-------|-----------|--------|----------|
| Store Icon [REQUIRED] | 128×128 PNG | ✅ Ready | `icons/icon-128.png` |
| Screenshot 1 [REQUIRED] | 1280×800 or 640×400 | ⬜ Not created | |
| Screenshot 2 [RECOMMENDED] | 1280×800 or 640×400 | ⬜ Not created | |
| Screenshot 3 [RECOMMENDED] | 1280×800 or 640×400 | ⬜ Not created | |
| Small Promo Tile [RECOMMENDED] | 440×280 | ⬜ Not created | |

### Screenshot Notes
* **Screenshot 1**: Active popup displaying the "Generator" tab on an X/Twitter thread, showcasing the "Generate Skill" button and neon-green dark mode glassmorphism UI.
* **Screenshot 2**: "Settings" tab displaying the local workspace path configurations and the Advanced collapsible section.
* **Screenshot 3**: A side-by-side view showing a saved custom skill markdown file imported into Claude Code or Cursor.

---

## Permissions Justification

Every permission used in our manifest is strictly scoped to the absolute minimum needed to provide a fluid user experience:

| Permission | Type | Justification |
|------------|------|---------------|
| `activeTab` | permissions | Required to read the URL and content of the currently focused tab to perform skill extraction when the user clicks the action icon. |
| `scripting` | permissions | Required to safely inject a helper DOM parser on the active web page to extract tweet text content. |
| `nativeMessaging` | permissions | Required to communicate with our secure local python companion script (`save_skill.py`) to write generated skill files directly to the user's project directories. |
| `storage` | permissions | Required to save settings such as preferred developer systems, connection modes, and local workspace paths. |
| `tabs` | permissions | Required to extract active tab's metadata (URL and Title) during generator initialization to pre-fill the workspace scope. |
| `downloads` | permissions | Optional fallback mechanism to let users download skill files directly if they choose to bypass the native helper. |
| `identity` | permissions | Required to handle Google Sign-In securely using Google OAuth and authenticate usage quotas. |
| `https://x.com/*` | host_permissions | Allows content parsing on X.com to retrieve developer threads. |
| `https://twitter.com/*` | host_permissions | Allows content parsing on Twitter.com to retrieve developer threads. |
| `https://tweet2skill.hero-apps.com/*` | host_permissions | Secure communication with our production web landing page and license portal. |
| `https://accounts.google.com/*` | host_permissions | Allows secure validation of Google Identity OAuth tokens. |

---

## Privacy & Data Use

### Data Collection
* **Does the extension collect user data?** Yes (strictly for quotas/licensing).

| Data Type | Collected? | Transmitted Off-Device? | Purpose | Shared with Third Parties? |
|-----------|-----------|------------------------|---------|---------------------------|
| Authentication info | Yes | Yes | Validates login token (ID Token) with Google to verify usage limits. | No |
| Personally identifiable info | Yes | Yes | Displaying user's email in the Account tab and managing quota. | No |
| Web history | No | No | N/A | No |

### Data Use Certification
- [x] Data is NOT sold to third parties
- [x] Data is NOT used for purposes unrelated to the extension's core functionality
- [x] Data is NOT used for creditworthiness or lending purposes

---

## Privacy Policy

**Privacy Policy URL** [REQUIRED]
`https://tweet2skill.hero-apps.com/privacy`

---

## Distribution

* **Visibility**: Public
* **Regions**: All regions
* **Pricing**: Free to try (freemium limits) with optional Pro upgrade.

---

## Developer Info

**Publisher Name** [REQUIRED]
Hero Apps

**Contact Email** [REQUIRED]
support@hero-apps.com

**Support URL / Email** [RECOMMENDED]
support@hero-apps.com

**Homepage URL** [RECOMMENDED]
`https://tweet2skill.hero-apps.com`

---

## Version History

| Version | Date | Changes | Status |
|---------|------|---------|--------|
| 1.1.1 | 2026-06-25 | Stabilized extension popup, added direct custom Google OAuth Client ID configurations, and synced directories. | Draft |
