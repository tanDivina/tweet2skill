// background.js — Handles background identity authentication to survive popup closure.

const DEFAULT_API_BASE = 'https://tweetskill.vercel.app';

async function getApiBase() {
  const { apiBase } = await chrome.storage.local.get('apiBase');
  return apiBase || DEFAULT_API_BASE;
}

async function _getClientId() {
  const { googleClientId } = await chrome.storage.local.get('googleClientId');
  return googleClientId || '238463452910-arlikd85im7mak8rkrkqdk51a5g00va6.apps.googleusercontent.com';
}

function generateNonce(length = 32) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const values = crypto.getRandomValues(new Uint8Array(length));
  return Array.from(values, v => chars[v % chars.length]).join('');
}

// Listen for messages from the popup to start the OAuth login
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[background] Received message:', message);
  if (message.action === 'loginWithGoogle') {
    console.log('[background] Initiating Google login flow...');
    loginWithGoogle()
      .then(data => {
        console.log('[background] Login successful! Returning user session:', data);
        sendResponse({ success: true, data });
      })
      .catch(err => {
        console.error('[background] Login failed error:', err);
        sendResponse({ success: false, error: err.message });
      });
    return true; // Keep message channel open for async response
  }
});

async function loginWithGoogle() {
  const redirectUri = chrome.identity.getRedirectURL();
  const nonce = generateNonce();
  const clientId = await _getClientId();

  console.log('[background] Redirect URI:', redirectUri);
  console.log('[background] Client ID:', clientId);

  await chrome.storage.local.set({
    lastAuthStatus: 'initiating',
    lastAuthError: null,
    lastAuthTimestamp: Date.now()
  });

  const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  authUrl.searchParams.set('client_id', clientId);
  authUrl.searchParams.set('response_type', 'id_token');
  authUrl.searchParams.set('redirect_uri', redirectUri);
  authUrl.searchParams.set('scope', 'email profile openid');
  authUrl.searchParams.set('nonce', nonce);
  authUrl.searchParams.set('prompt', 'select_account');

  return new Promise((resolve, reject) => {
    chrome.identity.launchWebAuthFlow(
      { url: authUrl.toString(), interactive: true },
      async (redirectUrl) => {
        if (chrome.runtime.lastError) {
          const errorMsg = chrome.runtime.lastError.message;
          console.error('[background] launchWebAuthFlow runtime error:', errorMsg);
          await chrome.storage.local.set({
            lastAuthStatus: 'failed',
            lastAuthError: `Google Identity Error: ${errorMsg}`
          });
          return reject(new Error(errorMsg));
        }
        if (!redirectUrl) {
          console.warn('[background] launchWebAuthFlow returned empty redirectUrl.');
          await chrome.storage.local.set({
            lastAuthStatus: 'failed',
            lastAuthError: 'Authentication was cancelled or redirected empty.'
          });
          return reject(new Error('Authentication was cancelled.'));
        }

        console.log('[background] launchWebAuthFlow successfully redirected:', redirectUrl);

        try {
          await chrome.storage.local.set({ lastAuthStatus: 'redirect_received' });

          // Extract id_token from the redirect hash fragment
          const hash = new URL(redirectUrl).hash.substring(1);
          const params = new URLSearchParams(hash);
          const idToken = params.get('id_token');

          if (!idToken) {
            console.error('[background] Could not find id_token in redirect URL hash.');
            await chrome.storage.local.set({
              lastAuthStatus: 'failed',
              lastAuthError: 'No id_token received in redirect from Google.'
            });
            return reject(new Error('No id_token received from Google.'));
          }

          console.log('[background] Extracted ID token successfully. Exchanging with backend...');
          await chrome.storage.local.set({ lastAuthStatus: 'exchanging_token' });

          // Exchange id_token with our backend
          const apiBase = await getApiBase();
          console.log('[background] Backend API Base:', apiBase);

          const res = await fetch(`${apiBase}/api/auth_google`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idToken })
          });

          console.log('[background] Backend HTTP response status:', res.status);

          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            const errMsg = err.message || `Auth failed (HTTP ${res.status})`;
            console.error('[background] Backend error details:', errMsg);
            await chrome.storage.local.set({
              lastAuthStatus: 'failed',
              lastAuthError: `Backend authentication failed: ${errMsg}`
            });
            return reject(new Error(errMsg));
          }

          const data = await res.json();
          console.log('[background] Token exchange response data parsed successfully.');

          // Store JWT and user info
          await chrome.storage.local.set({
            authJwt: data.token,
            userInfo: {
              id: data.user.id,
              email: data.user.email,
              name: data.user.name || '',
              tier: data.user.tier || 'free',
              avatar: data.user.picture || ''
            },
            lastAuthStatus: 'success',
            lastAuthError: null
          });

          console.log('[background] Saved session to local storage for user:', data.user.email);
          resolve(data);
        } catch (err) {
          console.error('[background] Unexpected error in callback processing:', err);
          await chrome.storage.local.set({
            lastAuthStatus: 'failed',
            lastAuthError: `Unexpected callback error: ${err.message}`
          });
          reject(err);
        }
      }
    );
  });
}

