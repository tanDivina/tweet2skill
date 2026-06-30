/**
 * Auth module for Tweet2Skill freemium system
 * Handles device identification, Google OAuth, JWT storage, usage tracking
 */
(function () {
  'use strict';

  const DEFAULT_API_BASE = 'https://tweetskill.vercel.app';

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  async function getApiBase() {
    const { apiBase } = await chrome.storage.local.get('apiBase');
    if (apiBase && apiBase.includes('hero-apps.com')) {
      await chrome.storage.local.remove('apiBase');
      return DEFAULT_API_BASE;
    }
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
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage({ action: 'loginWithGoogle' }, (response) => {
        if (chrome.runtime.lastError) {
          return reject(new Error(chrome.runtime.lastError.message));
        }
        if (response && response.success) {
          resolve(response.data);
        } else {
          reject(new Error(response ? response.error : 'Unknown authentication error.'));
        }
      });
    });
  }

  /** Get Google OAuth client ID from storage or use default production fallback */
  async function _getClientId() {
    const { googleClientId } = await chrome.storage.local.get('googleClientId');
    return googleClientId || '951467459639-gq3oefcvs74poea1atgee91u3nh44ni4.apps.googleusercontent.com';
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
