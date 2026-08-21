# Privacy Policy for Tweet2Skill

**Last Updated & Effective Date:** August 21, 2026  
**Product Name:** Tweet2Skill (Chrome Web Store Item ID: `gpggdojppnknejkhhggmpkfpdjmecnbb`)  
**Developer / Operator:** Dorien Van den Abbeele (Hero-Apps)  
**Website:** [https://tweet2skill.hero-apps.com](https://tweet2skill.hero-apps.com)  
**Privacy URL:** [https://tweet2skill.hero-apps.com/privacy](https://tweet2skill.hero-apps.com/privacy)  

---

## 1. Information We Collect

Tweet2Skill operates on a privacy-first, local-first architecture. We collect only the minimum necessary data to authenticate accounts, enforce credit quotas, and convert user-selected text into structured developer skills:

1. **Identification & Authentication Data (Cloud Mode):**
   - **Google Account Profile:** Email address, display name, and profile picture URL retrieved via Google OAuth when signing in.
   - **Session Tokens:** Temporary Google ID tokens and signed JWT tokens to verify access to backend API endpoints.

2. **User-Initiated Web Content & Thread Data:**
   - When and only when you explicitly click "Turn into Skill" or highlight text, the extension extracts the text content, post author handle, timestamp, and structure of the active tab (e.g. X/Twitter thread or technical documentation page).
   - Source URL and page title to generate citation metadata in the output skill.

3. **Client-Side Preferences & API Keys (Local Storage):**
   - **Custom API Keys (BYOK Mode):** If you enter a custom Gemini API key, it is stored strictly on your local device in `chrome.storage.local`. It is never sent to our servers.
   - User settings (target AI agent format, local directory path, Deep Thread toggle).

4. **Technical & Diagnostic Data:**
   - Account ID and generation counter keys (daily/monthly) stored in Redis to enforce quota limits and verify Pro credit balances.
   - Feedback submissions (message, feedback type, optional email, extension version).

---

## 2. How We Process and Use Your Data

- **Skill Generation:** Sending user-extracted tweet/webpage text to Google Gemini AI models to format structured markdown skills.
- **Account & Access Control:** Authenticating user identity and managing login sessions.
- **Quota & Billing:** Tracking daily free credits and one-time purchased Pro credit packs.
- **Local File Syncing:** Communicating with local Python helper (`save_skill.py`) to save generated files directly to the user's project directory.
- **Support:** Diagnosing and resolving bugs reported through feedback.

### Policy Certifications:
- We do **NOT** sell, rent, lease, or monetize user data.
- We do **NOT** use user data for advertising, marketing, or behavioral tracking.
- We do **NOT** use user data for creditworthiness, lending, or background screening.
- We do **NOT** track or record general web browsing history.

---

## 3. Data Storage, Security & Retention

- **Client-Side:** Preferences, local paths, and BYOK Gemini API keys reside exclusively in `chrome.storage.local`.
- **Cloud Database (Upstash Redis):** Account records (email, name, tier, credit balances) and rate limits are stored in an encrypted Redis database.
- **Ephemeral Processing:** Raw webpage content and tweet text sent to `/api/generate` are processed entirely in memory during the request and are **not permanently stored**.
- **Retention Schedule:**
  - Account records & Pro credit ledgers are kept until account deletion is requested.
  - Rate limit counters expire automatically after 24 hours (daily) / 30 days (monthly).
  - Feedback entries are retained for a maximum of 90 days.

---

## 4. Third-Party Sharing & Service Providers

| Service Provider | Data Shared | Purpose | Privacy Link |
| :--- | :--- | :--- | :--- |
| **Google Identity Services** | OAuth credentials, email, profile name | User authentication | [Google Privacy](https://policies.google.com/privacy) |
| **Google Gemini API** | Extracted tweet/page text | AI LLM inference (not used to train public models) | [Google Cloud Privacy](https://cloud.google.com/terms/cloud-privacy-notice) |
| **Stripe Inc.** | Transaction ID, billing email | Secure payment processing for Pro credits | [Stripe Privacy](https://stripe.com/privacy) |
| **Upstash Inc.** | User ID, email, credit balances | Encrypted cloud database storage | [Upstash Privacy](https://upstash.com/trust/privacy.pdf) |
| **Vercel Inc.** | Request headers (IP, User-Agent) | Serverless hosting infrastructure | [Vercel Privacy](https://vercel.com/legal/privacy-policy) |

---

## 5. Chrome Extension Permissions Justifications

- **`activeTab`**: Accesses the active tab URL/title only when the user explicitly clicks the extension icon.
- **`scripting`**: Executes the DOM parser to extract educational tweet/article text.
- **`nativeMessaging`**: Communicates with the local Python helper (`save_skill.py`) to save files to local folders.
- **`storage`**: Persists user settings, target AI system, and BYOK API keys locally.
- **`tabs`**: Reads tab metadata to pre-fill the workspace scope during popup open.
- **`downloads`**: Browser download fallback for skill files.
- **`identity`**: Performs Google OAuth sign-in.
- **Host Permissions (`x.com`, `twitter.com`, `tweet2skill.hero-apps.com`, `accounts.google.com`)**: Enables DOM reading on X, API calls to the Tweet2Skill backend, and Google OAuth exchange.

---

## 6. User Rights & Data Deletion

Users can request full access, export, or permanent deletion of their account data:
- **Local Data Deletion:** Clear extension storage or uninstall the extension.
- **Cloud Account Deletion:** Email **`support@hero-apps.com`** with the subject *"Tweet2Skill Data Deletion Request"*. All records will be permanently erased from our database within 30 days.

---

## 7. Contact Us

- **Developer:** Dorien Van den Abbeele (Hero-Apps)
- **Support Email:** `support@hero-apps.com`
- **Website:** [https://tweet2skill.hero-apps.com](https://tweet2skill.hero-apps.com)
- **X / Twitter:** [@dorienvibecodes](https://x.com/dorienvibecodes)
