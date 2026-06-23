/**
 * Auth module for Tweet2Skill freemium system
 * Handles device identification, Google OAuth, JWT storage, usage tracking
 */
(function () {
  'use strict';

  const DEFAULT_API_BASE = 'https://tweet2skill.hero-apps.com';

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  async function getApiBase() {
    const { apiBase } = await chrome.storage.local.get('apiBase');
    return apiBase || DEFAULT_API_BASE;
  }

  function generateNonce(length = 32) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const values = crypto.getRandomValues(new Uint8Array(length));
    return Array.from(values, v => chars[v % chars.length]).join('');
  }

  // ---------------------------------------------------------------------------
  // Device ID — persistent anonymous identifier
  // ---------------------------------------------------------------------------

  async function getDeviceId() {
    const { deviceId } = await chrome.storage.local.get('deviceId');
    if (deviceId) return deviceId;

    const newId = crypto.randomUUID();
    await chrome.storage.local.set({ deviceId: newId });
    return newId;
  }

  // ---------------------------------------------------------------------------
  // Google OAuth — uses chrome.identity.launchWebAuthFlow
  // ---------------------------------------------------------------------------

  async function loginWithGoogle() {
    const redirectUri = chrome.identity.getRedirectURL();
    const nonce = generateNonce();
    const clientId = await _getClientId();

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
            return reject(new Error(chrome.runtime.lastError.message));
          }
          if (!redirectUrl) {
            return reject(new Error('Authentication was cancelled.'));
          }

          try {
            // Extract id_token from the redirect hash fragment
            const hash = new URL(redirectUrl).hash.substring(1);
            const params = new URLSearchParams(hash);
            const idToken = params.get('id_token');

            if (!idToken) {
              return reject(new Error('No id_token received from Google.'));
            }

            // Exchange id_token with our backend
            const apiBase = await getApiBase();
            const res = await fetch(`${apiBase}/api/auth_google`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ idToken })
            });

            if (!res.ok) {
              const err = await res.json().catch(() => ({}));
              return reject(new Error(err.message || `Auth failed (HTTP ${res.status})`));
            }

            const data = await res.json();

            // Store JWT and user info
            await chrome.storage.local.set({
              authJwt: data.token,
              userInfo: {
                email: data.user.email,
                name: data.user.name || '',
                tier: data.user.tier || 'free',
                avatar: data.user.picture || ''
              }
            });

            resolve(data);
          } catch (err) {
            reject(err);
          }
        }
      );
    });
  }

  /** Get Google OAuth client ID from storage or use default placeholder */
  async function _getClientId() {
    const { googleClientId } = await chrome.storage.local.get('googleClientId');
    return googleClientId || 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com';
  }

  // ---------------------------------------------------------------------------
  // Logout
  // ---------------------------------------------------------------------------

  async function logout() {
    await chrome.storage.local.remove(['authJwt', 'userInfo']);
  }

  // ---------------------------------------------------------------------------
  // Auth Headers — returns appropriate headers for API calls
  // ---------------------------------------------------------------------------

  async function getAuthHeaders() {
    const deviceId = await getDeviceId();
    const { authJwt } = await chrome.storage.local.get('authJwt');

    const headers = {
      'Content-Type': 'application/json',
      'X-Device-Id': deviceId
    };

    if (authJwt) {
      headers['Authorization'] = `Bearer ${authJwt}`;
    }

    return headers;
  }

  // ---------------------------------------------------------------------------
  // Tier Detection
  // ---------------------------------------------------------------------------

  async function getUserTier() {
    const { userInfo, apiKey } = await chrome.storage.local.get(['userInfo', 'apiKey']);

    if (userInfo && userInfo.tier === 'pro') return 'pro';
    if (apiKey && apiKey.trim().length > 0) return 'byok';
    return 'free';
  }

  // ---------------------------------------------------------------------------
  // User Info
  // ---------------------------------------------------------------------------

  async function getUserInfo() {
    const { userInfo } = await chrome.storage.local.get('userInfo');
    return userInfo || null;
  }

  // ---------------------------------------------------------------------------
  // Usage Tracking
  // ---------------------------------------------------------------------------

  async function fetchUsage() {
    try {
      const apiBase = await getApiBase();
      const headers = await getAuthHeaders();

      const res = await fetch(`${apiBase}/api/usage`, {
        method: 'GET',
        headers
      });

      if (!res.ok) {
        console.warn('Usage fetch failed:', res.status);
        return { daily: 0, monthly: 0, limits: { daily: 10, monthly: 100 } };
      }

      const data = await res.json();

      // Cache locally for offline display
      await chrome.storage.local.set({ cachedUsage: data });

      return data;
    } catch (err) {
      console.warn('Usage fetch error:', err);
      // Return cached or defaults
      const { cachedUsage } = await chrome.storage.local.get('cachedUsage');
      return cachedUsage || { daily: 0, monthly: 0, limits: { daily: 10, monthly: 100 } };
    }
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  window.Auth = {
    getDeviceId,
    loginWithGoogle,
    logout,
    getAuthHeaders,
    getUserTier,
    getUserInfo,
    fetchUsage,
    getApiBase,
    DEFAULT_API_BASE
  };
})();
