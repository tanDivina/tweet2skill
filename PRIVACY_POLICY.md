# Privacy Policy for Tweet2Skill

Last updated: 2026-06-25

At Tweet2Skill, we respect your privacy and are committed to protecting any information processed by our Google Chrome Extension ("Tweet2Skill"). This Privacy Policy explains what data we process, how we secure it, and your rights as a user.

---

## 1. What Data We Process

Tweet2Skill is designed with a "Privacy-First, Local-First" philosophy. We collect and process the absolute minimum amount of information required to verify licenses and execute core features:

* **Authentication & Identity Information**: When you log in with Google, we process your Google user ID, email address, and name. This is strictly used to authenticate your account, check your subscription tier (e.g., Free vs. Pro), and manage your daily usage quotas.
* **API Keys & Settings**: If you choose to "Bring Your Own Key" (BYOK) for Gemini, your API key and settings (such as local workspace paths) are saved strictly inside your browser's local, encrypted storage (`chrome.storage.local`). They are never transmitted to our servers or any third parties.
* **Extracted Website Content**: When you click "Generate Skill," our extension safely extracts the text of the active tab (such as a developer thread on X/Twitter) and securely sends it to our Vercel backend (`https://tweetskill.vercel.app`) to parse it into markdown. We do not store or retain this extracted content on our servers after the markdown generation is complete.

---

## 2. How Data Is Stored & Secured

* **Local Storage**: Your personal settings, Gemini API keys, local workspace paths, and active preferences remain entirely on your own device inside the sandboxed environment provided by Chrome.
* **Server-Side Data**: Your user account profile (email and purchase/subscription status) is stored securely on our backend cloud database (Upstash Redis) and is encrypted in transit using SSL/TLS.

---

## 3. Third-Party Services We Use

We utilize the following secure third-party platforms to power our premium workflows:

* **Google Identity Services**: For secure, passwordless authentication using Google Sign-In.
  * [Google Privacy Policy](https://policies.google.com/privacy)
* **Google Gemini API**: To process website parsing when using cloud tiers.
  * [Google Gemini Privacy Terms](https://ai.google.dev/terms)
* **Vercel**: For secure, high-speed hosting of our backend APIs.
  * [Vercel Privacy Policy](https://vercel.com/legal/privacy-policy)
* **Lemon Squeezy**: For secure payment processing, subscriptions, and merchant licensing.
  * [Lemon Squeezy Privacy Policy](https://www.lemonsqueezy.com/privacy)

---

## 4. Data Sharing & Selling

**We do NOT sell, lease, rent, or share your personal data with third-party advertisers or marketers.** 

Your data is strictly processed to provide the functional services of the Tweet2Skill extension.

---

## 5. Data Retention & Deletion

We keep your account profile data (email and subscription tier) as long as your account is active. 

* **To delete your account or wipe all data**: Simply uninstall the extension to clear all local settings, and email us at `support@hero-apps.com` to request a permanent deletion of your profile from our backend database. We will process your deletion request within 48 hours.

---

## 6. Changes to This Policy

We may update this Privacy Policy from time to time. Any changes will be posted on this page, and we will update the "Last updated" date at the top.

---

## 7. Contact Us

If you have any questions or concerns regarding your privacy, please reach out to us:

* **Email**: support@hero-apps.com
* **Website**: [https://tweet2skill.hero-apps.com](https://tweet2skill.hero-apps.com)
