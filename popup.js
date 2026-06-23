document.addEventListener('DOMContentLoaded', async () => {
  // --- UI Elements ---
  const tabGenerator = document.getElementById('tab-generator');
  const tabSettings = document.getElementById('tab-settings');
  const tabAccount = document.getElementById('tab-account');

  const sectGenerator = document.getElementById('sect-generator');
  const sectSettings = document.getElementById('sect-settings');
  const sectAccount = document.getElementById('sect-account');

  const activeUrlSpan = document.getElementById('active-url');
  const scopeGlobal = document.getElementById('scope-global');
  const scopeWorkspace = document.getElementById('scope-workspace');
  const scopeHelp = document.getElementById('scope-help');
  
  const btnGenerate = document.getElementById('btn-generate');
  const btnText = btnGenerate ? btnGenerate.querySelector('.btn-text') : null;
  const btnLoader = btnGenerate ? btnGenerate.querySelector('.btn-loader') : null;

  const statusContainer = document.getElementById('status-container');
  const statusMsg = statusContainer ? statusContainer.querySelector('.status-message') : null;
  const statusIcon = statusContainer ? statusContainer.querySelector('.status-icon') : null;

  const apiKeyInput = document.getElementById('api-key-input');
  const btnToggleKey = document.getElementById('btn-toggle-key');
  const workspaceInput = document.getElementById('workspace-input');
  const btnSaveSettings = document.getElementById('btn-save-settings');

  const connLocal = document.getElementById('conn-local');
  const connCloud = document.getElementById('conn-cloud');
  const cloudUrlInput = document.getElementById('cloud-url-input');
  const groupCloudUrl = document.getElementById('group-cloud-url');
  const groupWorkspacePath = document.getElementById('group-workspace-path');

  // BYOK Collapsible
  const byokToggle = document.getElementById('byok-toggle');
  const byokContent = document.getElementById('byok-content');

  // Agent Systems
  const sysAntigravity = document.getElementById('system-antigravity');
  const sysClaude = document.getElementById('system-claude');
  const sysCursor = document.getElementById('system-cursor');
  const sysWindsurf = document.getElementById('system-windsurf');
  const sysCopilot = document.getElementById('system-copilot');

  // Upgrade Banner
  const upgradeBanner = document.getElementById('upgrade-banner');
  const btnUpgradeBanner = document.getElementById('btn-upgrade-banner');
  const btnByokBanner = document.getElementById('btn-byok-banner');

  // Account Tab Elements
  const loggedOutDiv = document.getElementById('account-logged-out');
  const loggedInDiv = document.getElementById('account-logged-in');
  const btnGoogleSignin = document.getElementById('btn-google-signin');
  const btnLogout = document.getElementById('btn-logout');
  const btnUpgradePro = document.getElementById('btn-upgrade-pro');
  
  const accountAvatar = document.getElementById('account-avatar');
  const accountEmail = document.getElementById('account-email');
  const tierBadge = document.getElementById('tier-badge');

  // Usage Progress
  const usageDailyText = document.getElementById('usage-daily-text');
  const usageDailyBar = document.getElementById('usage-daily-bar');
  const usageMonthlyText = document.getElementById('usage-monthly-text');
  const usageMonthlyBar = document.getElementById('usage-monthly-bar');

  // App State
  let activeTabUrl = '';
  let activeTabTitle = '';
  let currentScope = 'global'; // 'global' or 'workspace'
  let currentSystem = 'antigravity'; // 'antigravity', 'claude', 'cursor', 'windsurf', 'copilot'
  let currentConnMode = 'local'; // 'local' or 'cloud'

  // --- Initialize App ---
  // (Initialization code moved to non-blocking init() function at the end)


  // --- Tab Navigation ---
  function switchTab(activeTab, activeSect) {
    [tabGenerator, tabSettings, tabAccount].forEach(t => {
      if (t) t.classList.remove('active');
    });
    [sectGenerator, sectSettings, sectAccount].forEach(s => {
      if (s) s.classList.remove('active');
    });
    if (activeTab) activeTab.classList.add('active');
    if (activeSect) activeSect.classList.add('active');
    hideStatus();
  }

  if (tabGenerator) tabGenerator.addEventListener('click', () => switchTab(tabGenerator, sectGenerator));
  if (tabSettings) tabSettings.addEventListener('click', () => switchTab(tabSettings, sectSettings));
  if (tabAccount) tabAccount.addEventListener('click', () => switchTab(tabAccount, sectAccount));

  // --- BYOK Collapsible ---
  if (byokToggle && byokContent) {
    byokToggle.addEventListener('click', () => {
      byokToggle.classList.toggle('open');
      byokContent.classList.toggle('open');
    });
  }

  // --- Toggle Password Visibility ---
  if (btnToggleKey && apiKeyInput) {
    btnToggleKey.addEventListener('click', () => {
      if (apiKeyInput.type === 'password') {
        apiKeyInput.type = 'text';
        btnToggleKey.innerHTML = `
          <svg class="eye-icon closed-eye" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
            <line x1="1" y1="1" x2="23" y2="23"></line>
          </svg>
        `;
      } else {
        apiKeyInput.type = 'password';
        btnToggleKey.innerHTML = `
          <svg class="eye-icon open-eye" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
        `;
      }
    });
  }

  // --- Save Settings ---
  if (btnSaveSettings) {
    btnSaveSettings.addEventListener('click', async () => {
      const key = apiKeyInput.value.trim();
      const wsPath = workspaceInput.value.trim();
      const cUrl = cloudUrlInput.value.trim();
      
      await chrome.storage.local.set({ 
        apiKey: key, 
        workspacePath: wsPath,
        connectionMode: currentConnMode,
        cloudUrl: cUrl
      });
      
      showStatus('success', 'Settings saved successfully!', '✅');
      await refreshUI();
      
      setTimeout(() => {
        if (tabGenerator) tabGenerator.click();
      }, 1000);
    });
  }

  // --- Scope Toggle Buttons ---
  if (scopeGlobal) {
    scopeGlobal.addEventListener('click', () => {
      currentScope = 'global';
      chrome.storage.local.set({ scope: currentScope });
      updateScopeUI();
    });
  }
 
  if (scopeWorkspace) {
    scopeWorkspace.addEventListener('click', () => {
      currentScope = 'workspace';
      chrome.storage.local.set({ scope: currentScope });
      updateScopeUI();
    });
  }

  // --- Connection Mode Toggles ---
  if (connLocal) {
    connLocal.addEventListener('click', () => {
      currentConnMode = 'local';
      chrome.storage.local.set({ connectionMode: currentConnMode });
      updateConnModeUI();
    });
  }

  if (connCloud) {
    connCloud.addEventListener('click', () => {
      currentConnMode = 'cloud';
      chrome.storage.local.set({ connectionMode: currentConnMode });
      updateConnModeUI();
    });
  }

  // --- Agent Systems Click Routing ---
  const systems = [sysAntigravity, sysClaude, sysCursor, sysWindsurf, sysCopilot];
  systems.forEach(btn => {
    if (btn) {
      btn.addEventListener('click', async () => {
        const selected = btn.getAttribute('data-system');
        const tier = await Auth.getUserTier();
        
        // Gate Cursor, Windsurf, Copilot to Pro
        if (['cursor', 'windsurf', 'copilot'].includes(selected) && tier !== 'pro') {
          showStatus('warning', 'Cursor, Windsurf, and Copilot formats are exclusive to Pro tier users.', '⭐');
          if (upgradeBanner) upgradeBanner.classList.remove('hidden');
          return;
        }

        currentSystem = selected;
        chrome.storage.local.set({ system: currentSystem });
        updateSystemUI();
        updateScopeUI();
      });
    }
  });

  // --- Upgrade Action Routing ---
  const handleUpgrade = () => {
    chrome.tabs.create({ url: 'https://tweet2skill.hero-apps.com/#pricing' });
  };

  if (btnUpgradePro) btnUpgradePro.addEventListener('click', handleUpgrade);
  if (btnUpgradeBanner) btnUpgradeBanner.addEventListener('click', handleUpgrade);

  if (btnByokBanner) {
    btnByokBanner.addEventListener('click', () => {
      switchTab(tabSettings, sectSettings);
      if (byokToggle && byokContent && !byokToggle.classList.contains('open')) {
        byokToggle.classList.add('open');
        byokContent.classList.add('open');
      }
      if (apiKeyInput) {
        setTimeout(() => apiKeyInput.focus(), 150);
      }
    });
  }

  // --- Sign-in / Log-out Actions ---
  if (btnGoogleSignin) {
    btnGoogleSignin.addEventListener('click', async () => {
      try {
        hideStatus();
        btnGoogleSignin.disabled = true;
        const textSpan = btnGoogleSignin.querySelector('span');
        const origText = textSpan ? textSpan.textContent : 'Sign in with Google';
        if (textSpan) textSpan.textContent = 'Signing in...';

        await Auth.loginWithGoogle();
        
        if (textSpan) textSpan.textContent = origText;
        btnGoogleSignin.disabled = false;
        
        showStatus('success', 'Logged in successfully with Google!', '🚀');
        await refreshUI();
      } catch (err) {
        btnGoogleSignin.disabled = false;
        const textSpan = btnGoogleSignin.querySelector('span');
        if (textSpan) textSpan.textContent = 'Sign in with Google';
        showStatus('error', `Login failed: ${err.message}`, '❌');
      }
    });
  }

  if (btnLogout) {
    btnLogout.addEventListener('click', async () => {
      hideStatus();
      await Auth.logout();
      showStatus('success', 'Logged out successfully.', '✅');
      await refreshUI();
    });
  }

  // --- Detect Active Tab URL ---
  // (Active tab detection moved to non-blocking init() function at the end)

  // --- Generate Skill Trigger ---
  if (btnGenerate) {
    btnGenerate.addEventListener('click', async () => {
      hideStatus();
      
      const { apiKey, workspacePath, connectionMode, cloudUrl } = await chrome.storage.local.get([
        'apiKey', 'workspacePath', 'connectionMode', 'cloudUrl'
      ]);
      
      const wsPath = workspacePath || '';
      const connMode = connectionMode || 'local';
      const tier = await Auth.getUserTier();
      const usage = await Auth.fetchUsage();

      // Check daily free limits
      if (tier === 'free' && usage && usage.daily && usage.daily.used >= usage.daily.limit) {
        showStatus('error', 'Daily limit reached. Bring your own key in Settings or upgrade to Pro.', '⚠️');
        if (upgradeBanner) upgradeBanner.classList.remove('hidden');
        return;
      }

      // Check Pro format locks
      if (['cursor', 'windsurf', 'copilot'].includes(currentSystem) && tier !== 'pro') {
        showStatus('error', 'Selected format requires a Pro subscription.', '⚠️');
        if (upgradeBanner) upgradeBanner.classList.remove('hidden');
        return;
      }

      // Check Workspace Scope Local requirements
      if (currentScope === 'workspace' && connMode === 'local' && !wsPath) {
        showStatus('error', 'Please configure your Local Workspace Path in Settings to use Workspace scope.', '⚠️');
        switchTab(tabSettings, sectSettings);
        return;
      }

      setGenerating(true);

      try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab) {
          throw new Error('No active tab found.');
        }

        // Inject content extraction script
        const injectionResults = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: extractPageContent
        });

        if (!injectionResults || !injectionResults[0] || !injectionResults[0].result) {
          throw new Error('Could not extract content from the page.');
        }

        const { type, title, content } = injectionResults[0].result;

        if (!content || content.trim().length === 0) {
          throw new Error('Selected page content is empty.');
        }

        if (connMode === 'local') {
          // Native Bridge payload
          const hostName = 'com.antigravity.linker';
          const { authJwt } = await chrome.storage.local.get('authJwt');
          
          const payload = {
            url: tab.url,
            title: title || tab.title || 'Untitled Page',
            contentType: type,
            content: content,
            scope: currentScope,
            workspacePath: wsPath,
            agentSystem: currentSystem,
            deviceId: await Auth.getDeviceId(),
            authToken: authJwt || ''
          };

          if (tier === 'byok' && apiKey) {
            payload.apiKey = apiKey;
          }

          chrome.runtime.sendNativeMessage(hostName, payload, (response) => {
            setGenerating(false);
            if (chrome.runtime.lastError) {
              console.error(chrome.runtime.lastError);
              showStatus('error', `Native Bridge Error: ${chrome.runtime.lastError.message}. Make sure the host is installed.`, '❌');
            } else if (response && response.status === 'done') {
              showStatus('success', response.message.replace(/\n/g, '<br>'), '🚀');
              setTimeout(refreshUI, 1000);
            } else {
              const errMsg = response ? response.message : 'Unknown error from native host.';
              showStatus('error', `Error: ${errMsg}`, '❌');
            }
          });
        } else {
          // Cloud Vercel payload
          if (!cloudUrl) {
            throw new Error('Vercel Endpoint URL is missing. Configure it in Settings.');
          }

          let apiEndpoint = cloudUrl.trim();
          if (!apiEndpoint.startsWith('http://') && !apiEndpoint.startsWith('https://')) {
            apiEndpoint = 'https://' + apiEndpoint;
          }
          if (!apiEndpoint.endsWith('/api/generate') && !apiEndpoint.endsWith('/api/generate/')) {
            apiEndpoint = apiEndpoint.replace(/\/$/, '') + '/api/generate';
          }

          const payload = {
            url: tab.url,
            title: title || tab.title || 'Untitled Page',
            contentType: type,
            content: content,
            agentSystem: currentSystem
          };

          if (tier === 'byok' && apiKey) {
            payload.apiKey = apiKey;
          }

          const headers = await Auth.getAuthHeaders();

          const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(payload)
          });

          if (!response.ok) {
            const errBody = await response.json().catch(() => ({}));
            throw new Error(errBody.message || `API returned HTTP ${response.status}`);
          }

          const resData = await response.json();
          setGenerating(false);

          if (resData.status === 'done' && resData.markdown) {
            // Determine friendly path display
            let targetPath = '';
            if (currentSystem === 'antigravity') {
              targetPath = currentScope === 'global' 
                ? `~/.gemini/config/skills/${resData.slug}/SKILL.md` 
                : `.agents/skills/${resData.slug}/SKILL.md`;
            } else if (currentSystem === 'claude') {
              targetPath = currentScope === 'global' 
                ? `~/.claude/rules/${resData.slug}.md` 
                : `.claude/rules/${resData.slug}.md`;
            } else if (currentSystem === 'cursor') {
              targetPath = currentScope === 'global' 
                ? `~/.cursor/rules/${resData.slug}.md` 
                : `.cursor/rules/${resData.slug}.md`;
            } else if (currentSystem === 'windsurf') {
              targetPath = currentScope === 'global' 
                ? `~/.windsurfrules` 
                : `.windsurfrules`;
            } else if (currentSystem === 'copilot') {
              targetPath = currentScope === 'global' 
                ? `~/.github/copilot-instructions.md` 
                : `.github/copilot-instructions.md`;
            }

            // Determine download filename
            let filename = '';
            if (currentSystem === 'antigravity') {
              filename = `${resData.slug}/SKILL.md`;
            } else if (currentSystem === 'claude' || currentSystem === 'cursor') {
              filename = `${resData.slug}.md`;
            } else if (currentSystem === 'windsurf') {
              filename = `.windsurfrules`;
            } else if (currentSystem === 'copilot') {
              filename = `copilot-instructions.md`;
            }

            const blobUrl = 'data:text/markdown;charset=utf-8,' + encodeURIComponent(resData.markdown);

            chrome.downloads.download({
              url: blobUrl,
              filename: filename,
              saveAs: true
            }, (downloadId) => {
              if (chrome.runtime.lastError) {
                showStatus('error', `Download failed: ${chrome.runtime.lastError.message}`, '❌');
              } else {
                const labelText = currentSystem === 'antigravity' ? 'SKILL PATH' : 'RULE PATH';
                const htmlContent = `
                  <div style="font-weight: 700; margin-bottom: 4px;">Generation Successful!</div>
                  <div style="font-size: 11px; opacity: 0.95; margin-bottom: 6px;">Save the downloaded file exactly to this path:</div>
                  <div style="background: rgba(0,0,0,0.4); padding: 6px; border-radius: 4px; font-family: monospace; font-size: 11px; word-break: break-all; border: 1px solid rgba(255,255,255,0.15); margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                    <span style="color: #a8ff35; font-weight: 500;">${targetPath}</span>
                    <button id="btn-copy-path" style="background: #ffffff; border: none; color: #000000; padding: 2px 8px; border-radius: 3px; cursor: pointer; font-size: 10px; font-family: var(--font-family); font-weight: 700; flex-shrink: 0; transition: all 0.2s;">COPY</button>
                  </div>
                `;
                showStatus('success', htmlContent, '🚀');
                
                const copyBtn = document.getElementById('btn-copy-path');
                if (copyBtn) {
                  copyBtn.addEventListener('click', () => {
                    navigator.clipboard.writeText(targetPath);
                    copyBtn.textContent = 'COPIED!';
                    copyBtn.style.background = '#a8ff35';
                    setTimeout(() => { 
                      copyBtn.textContent = 'COPY'; 
                      copyBtn.style.background = '#ffffff';
                    }, 1500);
                  });
                }
                setTimeout(refreshUI, 1000);
              }
            });
          } else {
            throw new Error(resData.message || 'Malformed response from Vercel API.');
          }
        }
      } catch (err) {
        setGenerating(false);
        showStatus('error', `Generation failed: ${err.message}`, '❌');
      }
    });
  }

  // --- Helper Functions ---

  async function checkAuthMe() {
    const { authJwt } = await chrome.storage.local.get('authJwt');
    if (!authJwt) return;

    try {
      const apiBase = await Auth.getApiBase();
      const headers = await Auth.getAuthHeaders();
      const res = await fetch(`${apiBase}/api/auth_me`, {
        method: 'GET',
        headers
      });

      if (res.ok) {
        const data = await res.json();
        if (data.status === 'ok' && data.user) {
          await chrome.storage.local.set({
            userInfo: {
              email: data.user.email,
              name: data.user.name || '',
              tier: data.user.tier || 'free',
              avatar: data.user.picture || ''
            }
          });
        }
      } else if (res.status === 401) {
        // Token has expired or is invalid
        await Auth.logout();
      }
    } catch (e) {
      console.warn('Failed to verify token on startup:', e);
    }
  }

  async function refreshUI() {
    const tier = await Auth.getUserTier();
    const userInfo = await Auth.getUserInfo();
    const usage = await Auth.fetchUsage();

    // 1. Update Header Badge
    const usageBadge = document.getElementById('usage-badge');
    const badgeText = usageBadge ? usageBadge.querySelector('.usage-badge-text') : null;
    
    if (usageBadge && badgeText) {
      if (tier === 'pro') {
        usageBadge.className = 'usage-badge is-pro';
        badgeText.textContent = 'PRO';
      } else if (tier === 'byok') {
        usageBadge.className = 'usage-badge is-byok';
        badgeText.textContent = 'BYOK';
      } else {
        const dailyUsed = (usage && usage.daily && usage.daily.used !== null) ? usage.daily.used : 0;
        const dailyLimit = (usage && usage.daily && usage.daily.limit !== null) ? usage.daily.limit : 10;
        usageBadge.className = 'usage-badge' + (dailyUsed >= dailyLimit - 2 ? ' near-limit' : '');
        badgeText.textContent = `${dailyUsed}/${dailyLimit}`;
      }
    }

    // 2. Lock / Unlock system toggle options based on tier
    systems.forEach(btn => {
      if (btn) {
        const system = btn.getAttribute('data-system');
        if (['cursor', 'windsurf', 'copilot'].includes(system)) {
          if (tier === 'pro') {
            btn.classList.remove('pro-locked');
          } else {
            btn.classList.add('pro-locked');
            // If the selected option got locked, fallback selection to antigravity
            if (btn.classList.contains('active')) {
              btn.classList.remove('active');
              currentSystem = 'antigravity';
              if (sysAntigravity) sysAntigravity.classList.add('active');
              chrome.storage.local.set({ system: currentSystem });
              updateSystemUI();
              updateScopeUI();
            }
          }
        }
      }
    });

    // 3. Toggle upgrade banner
    if (upgradeBanner) {
      if (tier === 'free' && usage && usage.daily && usage.daily.used >= usage.daily.limit) {
        upgradeBanner.classList.remove('hidden');
      } else {
        upgradeBanner.classList.add('hidden');
      }
    }

    // 4. Update Account Section Logged In/Out state
    if (userInfo && userInfo.email) {
      if (loggedOutDiv) loggedOutDiv.classList.add('hidden');
      if (loggedInDiv) loggedInDiv.classList.remove('hidden');

      if (accountEmail) accountEmail.textContent = userInfo.email;

      if (accountAvatar) {
        if (userInfo.avatar) {
          accountAvatar.innerHTML = `<img src="${userInfo.avatar}" alt="Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
        } else {
          const initial = userInfo.email.charAt(0).toUpperCase();
          accountAvatar.innerHTML = `<div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: var(--text-primary); font-size: 14px;">${initial}</div>`;
        }
      }

      if (tierBadge) {
        if (tier === 'pro') {
          tierBadge.className = 'tier-badge tier-pro';
          tierBadge.textContent = 'PRO';
        } else {
          tierBadge.className = 'tier-badge tier-free';
          tierBadge.textContent = 'FREE';
        }
      }

      if (btnUpgradePro) {
        if (tier === 'pro') {
          btnUpgradePro.classList.add('hidden');
        } else {
          btnUpgradePro.classList.remove('hidden');
        }
      }
    } else {
      if (loggedOutDiv) loggedOutDiv.classList.remove('hidden');
      if (loggedInDiv) loggedInDiv.classList.add('hidden');
    }

    // 5. Update Account Stats & Bars
    if (usageDailyText && usageDailyBar && usageMonthlyText && usageMonthlyBar) {
      if (tier === 'pro') {
        usageDailyText.textContent = 'Unlimited';
        usageDailyBar.style.width = '100%';

        const monthlyUsed = (usage && usage.monthly) ? usage.monthly.used : 0;
        const monthlyLimit = (usage && usage.monthly) ? usage.monthly.limit : 1250;
        usageMonthlyText.textContent = `${monthlyUsed} / ${monthlyLimit}`;
        const pct = Math.min(100, (monthlyUsed / monthlyLimit) * 100);
        usageMonthlyBar.style.width = `${pct}%`;
      } else if (tier === 'byok') {
        usageDailyText.textContent = 'Unlimited';
        usageDailyBar.style.width = '100%';
        usageMonthlyText.textContent = 'Unlimited';
        usageMonthlyBar.style.width = '100%';
      } else {
        const dailyUsed = (usage && usage.daily) ? usage.daily.used : 0;
        const dailyLimit = (usage && usage.daily) ? usage.daily.limit : 10;
        usageDailyText.textContent = `${dailyUsed} / ${dailyLimit}`;
        const dailyPct = Math.min(100, (dailyUsed / dailyLimit) * 100);
        usageDailyBar.style.width = `${dailyPct}%`;

        const monthlyUsed = (usage && usage.monthly) ? usage.monthly.used : 0;
        const monthlyLimit = (usage && usage.monthly) ? usage.monthly.limit : 1250;
        usageMonthlyText.textContent = `${monthlyUsed} / ${monthlyLimit}`;
        const monthlyPct = Math.min(100, (monthlyUsed / monthlyLimit) * 100);
        usageMonthlyBar.style.width = `${monthlyPct}%`;
      }
    }
  }

  function updateSystemUI() {
    systems.forEach(btn => {
      if (btn) {
        if (btn.getAttribute('data-system') === currentSystem) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      }
    });

    if (btnText) {
      if (currentSystem === 'antigravity') {
        btnText.textContent = 'Turn into Skill';
      } else {
        btnText.textContent = 'Turn into Rule';
      }
    }
  }
 
  function updateScopeUI() {
    if (!scopeHelp) return;

    if (currentScope === 'global') {
      if (scopeGlobal) scopeGlobal.classList.add('active');
      if (scopeWorkspace) scopeWorkspace.classList.remove('active');

      if (currentSystem === 'antigravity') {
        scopeHelp.textContent = 'Saves to ~/.gemini/config/skills/';
      } else if (currentSystem === 'claude') {
        scopeHelp.textContent = 'Saves to ~/.claude/rules/';
      } else if (currentSystem === 'cursor') {
        scopeHelp.textContent = 'Saves to ~/.cursor/rules/';
      } else if (currentSystem === 'windsurf') {
        scopeHelp.textContent = 'Appends to ~/.windsurfrules';
      } else if (currentSystem === 'copilot') {
        scopeHelp.textContent = 'Appends to ~/.github/copilot-instructions.md';
      }
    } else {
      if (scopeWorkspace) scopeWorkspace.classList.add('active');
      if (scopeGlobal) scopeGlobal.classList.remove('active');

      if (currentSystem === 'antigravity') {
        scopeHelp.textContent = 'Saves to project-folder/.agents/skills/';
      } else if (currentSystem === 'claude') {
        scopeHelp.textContent = 'Saves to project-folder/.claude/rules/';
      } else if (currentSystem === 'cursor') {
        scopeHelp.textContent = 'Saves to project-folder/.cursor/rules/';
      } else if (currentSystem === 'windsurf') {
        scopeHelp.textContent = 'Appends to project-folder/.windsurfrules';
      } else if (currentSystem === 'copilot') {
        scopeHelp.textContent = 'Appends to project-folder/.github/copilot-instructions.md';
      }
    }
  }

  function updateConnModeUI() {
    if (currentConnMode === 'local') {
      if (connLocal) connLocal.classList.add('active');
      if (connCloud) connCloud.classList.remove('active');
      if (groupWorkspacePath) groupWorkspacePath.style.display = 'block';
      if (groupCloudUrl) groupCloudUrl.style.display = 'none';
    } else {
      if (connCloud) connCloud.classList.add('active');
      if (connLocal) connLocal.classList.remove('active');
      if (groupWorkspacePath) groupWorkspacePath.style.display = 'none';
      if (groupCloudUrl) groupCloudUrl.style.display = 'block';
    }
  }

  function showStatus(type, message, iconText) {
    if (!statusContainer || !statusMsg || !statusIcon) return;

    statusContainer.className = `status-box ${type}`;
    statusMsg.innerHTML = message;
    
    let svgIcon = '';
    if (type === 'success') {
      svgIcon = `
        <svg class="status-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
      `;
    } else if (type === 'error') {
      svgIcon = `
        <svg class="status-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
      `;
    } else {
      svgIcon = `
        <svg class="status-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
      `;
    }
    statusIcon.innerHTML = svgIcon;
    statusContainer.classList.remove('hidden');
  }

  function hideStatus() {
    if (statusContainer) statusContainer.classList.add('hidden');
  }

  function setGenerating(isGenerating) {
    if (!btnGenerate || !btnText || !btnLoader) return;
    
    if (isGenerating) {
      btnGenerate.disabled = true;
      btnText.textContent = currentSystem === 'antigravity' ? 'Generating Skill...' : 'Generating Rule...';
      btnLoader.classList.remove('hidden');
    } else {
      btnGenerate.disabled = false;
      btnText.textContent = currentSystem === 'antigravity' ? 'Turn into Skill' : 'Turn into Rule';
      btnLoader.classList.add('hidden');
    }
  }

  // Content extraction function injected into the active tab
  function extractPageContent() {
    const selection = window.getSelection().toString().trim();
    if (selection) {
      return { type: 'selection', title: document.title, content: selection };
    }

    const url = window.location.href;
    const isTwitter = url.includes('x.com') || url.includes('twitter.com');

    if (isTwitter) {
      const urlParts = url.split('/');
      const statusIndex = urlParts.indexOf('status');
      let authorHandle = '';
      if (statusIndex > 1) {
        authorHandle = urlParts[statusIndex - 1].toLowerCase();
      }

      const tweets = Array.from(document.querySelectorAll('article[data-testid="tweet"]'));
      if (tweets.length > 0) {
        const threadText = [];

        tweets.forEach((tweet) => {
          const userDiv = tweet.querySelector('[data-testid="User-Name"]');
          const textDiv = tweet.querySelector('[data-testid="tweetText"]');
          if (textDiv) {
            const text = textDiv.innerText.trim();
            if (userDiv) {
              const handleMatch = userDiv.innerText.match(/@(\w+)/);
              const handle = handleMatch ? handleMatch[1].toLowerCase() : '';
              if (handle === authorHandle || !authorHandle) {
                threadText.push(text);
              }
            } else {
              threadText.push(text);
            }
          }
        });

        if (threadText.length > 0) {
          return {
            type: 'tweet',
            title: `Tweet/Thread by @${authorHandle || 'author'}`,
            content: threadText.join('\n\n---\n\n')
          };
        }
      }
    }

    // General fallback reader mode extraction
    const container = document.querySelector('article') || document.querySelector('main') || document.body;
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = container.innerHTML;
    
    const elementsToRemove = tempDiv.querySelectorAll('script, style, nav, footer, header, noscript, iframe');
    elementsToRemove.forEach(el => el.remove());
    
    let contentText = tempDiv.innerText.replace(/\s+/g, ' ').trim();
    
    if (contentText.length > 15000) {
      contentText = contentText.substring(0, 15000) + '\n\n... [Content Truncated due to Length]';
    }

    return {
      type: 'general',
      title: document.title,
      content: contentText
    };
  }

  // --- Async Initialization ---
  async function init() {
    try {
      // 1. Detect Active Tab URL
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab && tab.url) {
        activeTabUrl = tab.url;
        activeTabTitle = tab.title || '';
        if (activeUrlSpan) {
          activeUrlSpan.textContent = activeTabUrl;
          activeUrlSpan.title = activeTabUrl;
        }
      } else {
        if (activeUrlSpan) activeUrlSpan.textContent = 'No active tab detected';
      }
    } catch (err) {
      console.error('Failed to get active tab:', err);
      if (activeUrlSpan) activeUrlSpan.textContent = 'Error detecting page';
    }

    try {
      // 2. Initial verification of Auth token
      await checkAuthMe();

      // 3. Load settings from storage
      const settings = await chrome.storage.local.get([
        'apiKey', 'scope', 'workspacePath', 'system', 'connectionMode', 'cloudUrl'
      ]);

      if (apiKeyInput && settings.apiKey) apiKeyInput.value = settings.apiKey;
      if (workspaceInput) workspaceInput.value = settings.workspacePath || '';
      if (cloudUrlInput) cloudUrlInput.value = settings.cloudUrl || '';
      
      if (settings.scope) currentScope = settings.scope;
      if (settings.system) currentSystem = settings.system;
      if (settings.connectionMode) currentConnMode = settings.connectionMode;

      updateScopeUI();
      updateSystemUI();
      updateConnModeUI();
      
      // 4. Initial UI refresh (badge, bars, locks, banner)
      await refreshUI();
    } catch (err) {
      console.error('Error during startup initialization:', err);
    }
  }

  // Run initialization
  init();
});
