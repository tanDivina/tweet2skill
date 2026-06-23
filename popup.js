document.addEventListener('DOMContentLoaded', async () => {
  // UI Elements
  const tabGenerator = document.getElementById('tab-generator');
  const tabSettings = document.getElementById('tab-settings');
  const sectGenerator = document.getElementById('sect-generator');
  const sectSettings = document.getElementById('sect-settings');

  const activeUrlSpan = document.getElementById('active-url');
  const scopeGlobal = document.getElementById('scope-global');
  const scopeWorkspace = document.getElementById('scope-workspace');
  const scopeHelp = document.getElementById('scope-help');
  const btnGenerate = document.getElementById('btn-generate');
  const btnText = btnGenerate.querySelector('.btn-text');
  const btnLoader = btnGenerate.querySelector('.btn-loader');

  const statusContainer = document.getElementById('status-container');
  const statusMsg = statusContainer.querySelector('.status-message');
  const statusIcon = statusContainer.querySelector('.status-icon');

  const apiKeyInput = document.getElementById('api-key-input');
  const btnToggleKey = document.getElementById('btn-toggle-key');
  const workspaceInput = document.getElementById('workspace-input');
  const btnSaveSettings = document.getElementById('btn-save-settings');

  const systemAntigravity = document.getElementById('system-antigravity');
  const systemClaude = document.getElementById('system-claude');

  const connLocal = document.getElementById('conn-local');
  const connCloud = document.getElementById('conn-cloud');
  const cloudUrlInput = document.getElementById('cloud-url-input');
  const groupCloudUrl = document.getElementById('group-cloud-url');
  const groupWorkspacePath = document.getElementById('group-workspace-path');

  // App State
  let activeTabUrl = '';
  let activeTabTitle = '';
  let currentScope = 'global'; // 'global' or 'workspace'
  let currentSystem = 'antigravity'; // 'antigravity' or 'claude'
  let currentConnMode = 'local'; // 'local' or 'cloud'

  // Tab Navigation
  tabGenerator.addEventListener('click', () => {
    tabGenerator.classList.add('active');
    tabSettings.classList.remove('active');
    sectGenerator.classList.add('active');
    sectSettings.classList.remove('active');
    hideStatus();
  });

  tabSettings.addEventListener('click', () => {
    tabSettings.classList.add('active');
    tabGenerator.classList.remove('active');
    sectSettings.classList.add('active');
    sectGenerator.classList.remove('active');
    hideStatus();
  });

  // Toggle Password Visibility
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

  // Load Settings from Local Storage
  const settings = await chrome.storage.local.get(['apiKey', 'scope', 'workspacePath', 'system', 'connectionMode', 'cloudUrl']);
  if (settings.apiKey) {
    apiKeyInput.value = settings.apiKey;
  }
  workspaceInput.value = settings.workspacePath || '/Users/dorienvandenabbeele/TweetSkill';
  cloudUrlInput.value = settings.cloudUrl || '';
  if (settings.scope) {
    currentScope = settings.scope;
  }
  if (settings.system) {
    currentSystem = settings.system;
  }
  if (settings.connectionMode) {
    currentConnMode = settings.connectionMode;
  }
  updateScopeUI();
  updateSystemUI();
  updateConnModeUI();

  // Save Settings
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
    setTimeout(() => {
      tabGenerator.click();
    }, 1000);
  });

  // Scope Toggle Buttons
  scopeGlobal.addEventListener('click', () => {
    currentScope = 'global';
    chrome.storage.local.set({ scope: currentScope });
    updateScopeUI();
  });
 
  scopeWorkspace.addEventListener('click', () => {
    currentScope = 'workspace';
    chrome.storage.local.set({ scope: currentScope });
    updateScopeUI();
  });

  // System Toggle Buttons
  systemAntigravity.addEventListener('click', () => {
    currentSystem = 'antigravity';
    chrome.storage.local.set({ system: currentSystem });
    updateSystemUI();
    updateScopeUI();
  });

  systemClaude.addEventListener('click', () => {
    currentSystem = 'claude';
    chrome.storage.local.set({ system: currentSystem });
    updateSystemUI();
    updateScopeUI();
  });

  // Connection Mode Toggles
  connLocal.addEventListener('click', () => {
    currentConnMode = 'local';
    chrome.storage.local.set({ connectionMode: currentConnMode });
    updateConnModeUI();
  });

  connCloud.addEventListener('click', () => {
    currentConnMode = 'cloud';
    chrome.storage.local.set({ connectionMode: currentConnMode });
    updateConnModeUI();
  });

  function updateSystemUI() {
    if (currentSystem === 'antigravity') {
      systemAntigravity.classList.add('active');
      systemClaude.classList.remove('active');
      btnText.textContent = 'Turn into Skill';
    } else {
      systemClaude.classList.add('active');
      systemAntigravity.classList.remove('active');
      btnText.textContent = 'Turn into Rule';
    }
  }
 
  function updateScopeUI() {
    if (currentScope === 'global') {
      scopeGlobal.classList.add('active');
      scopeWorkspace.classList.remove('active');
      if (currentSystem === 'antigravity') {
        scopeHelp.textContent = 'Saves to ~/.gemini/config/skills/';
      } else {
        scopeHelp.textContent = 'Saves to ~/.claude/rules/';
      }
    } else {
      scopeWorkspace.classList.add('active');
      scopeGlobal.classList.remove('active');
      if (currentSystem === 'antigravity') {
        scopeHelp.textContent = 'Saves to project-folder/.agents/skills/';
      } else {
        scopeHelp.textContent = 'Saves to project-folder/.claude/rules/';
      }
    }
  }

  function updateConnModeUI() {
    if (currentConnMode === 'local') {
      connLocal.classList.add('active');
      connCloud.classList.remove('active');
      groupWorkspacePath.style.display = 'block';
      groupCloudUrl.style.display = 'none';
    } else {
      connCloud.classList.add('active');
      connLocal.classList.remove('active');
      groupWorkspacePath.style.display = 'none';
      groupCloudUrl.style.display = 'block';
    }
  }

  // Detect Active Tab URL
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url) {
      activeTabUrl = tab.url;
      activeTabTitle = tab.title || '';
      activeUrlSpan.textContent = activeTabUrl;
    } else {
      activeUrlSpan.textContent = 'No active tab detected';
    }
  } catch (err) {
    console.error('Failed to get active tab:', err);
    activeUrlSpan.textContent = 'Error detecting page';
  }

  // Helper functions for Status display
  function showStatus(type, message, iconText) {
    statusContainer.className = `status-box ${type}`;
    statusMsg.innerHTML = message; // Support HTML markup for the copy path box
    
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
    statusContainer.classList.add('hidden');
  }

  function setGenerating(isGenerating) {
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

  // Generate Skill Button Trigger
  btnGenerate.addEventListener('click', async () => {
    hideStatus();
    const { apiKey, workspacePath, connectionMode, cloudUrl } = await chrome.storage.local.get(['apiKey', 'workspacePath', 'connectionMode', 'cloudUrl']);
    const wsPath = workspacePath || '/Users/dorienvandenabbeele/TweetSkill';
    const connMode = connectionMode || 'local';

    if (!apiKey) {
      showStatus('error', 'Please configure your Gemini API Key in the Settings tab first.', '⚠️');
      tabSettings.click();
      return;
    }

    setGenerating(true);

    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) {
        throw new Error('No active tab found.');
      }

      // 1. Inject DOM script to extract content
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
        // 2a. Send payload to local native messaging host
        const hostName = 'com.antigravity.linker';
        const payload = {
          url: tab.url,
          title: title || tab.title || 'Untitled Page',
          contentType: type,
          content: content,
          apiKey: apiKey,
          scope: currentScope,
          workspacePath: wsPath,
          agentSystem: currentSystem
        };

        chrome.runtime.sendNativeMessage(hostName, payload, (response) => {
          setGenerating(false);
          if (chrome.runtime.lastError) {
            console.error(chrome.runtime.lastError);
            showStatus('error', `Native Bridge Error: ${chrome.runtime.lastError.message}. Make sure the host is installed.`, '❌');
          } else if (response && response.status === 'done') {
            showStatus('success', response.message, '🚀');
          } else {
            const errMsg = response ? response.message : 'Unknown error from native host.';
            showStatus('error', `Error: ${errMsg}`, '❌');
          }
        });
      } else {
        // 2b. Send payload to cloud Vercel API
        if (!cloudUrl) {
          throw new Error('Vercel Endpoint URL is missing. Set it in Settings.');
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
          apiKey: apiKey,
          agentSystem: currentSystem
        };

        const response = await fetch(apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          const errBody = await response.json().catch(() => ({}));
          throw new Error(errBody.message || `API returned HTTP ${response.status}`);
        }

        const resData = await response.json();
        setGenerating(false);

        if (resData.status === 'done' && resData.markdown) {
          // Determine the user-facing path based on system & scope
          let targetPath = '';
          if (currentSystem === 'antigravity') {
            targetPath = currentScope === 'global' 
              ? `~/.gemini/config/skills/${resData.slug}/SKILL.md` 
              : `.agents/skills/${resData.slug}/SKILL.md`;
          } else {
            targetPath = currentScope === 'global' 
              ? `~/.claude/rules/${resData.slug}.md` 
              : `.claude/rules/${resData.slug}.md`;
          }

          // Trigger file download
          const blobUrl = 'data:text/markdown;charset=utf-8,' + encodeURIComponent(resData.markdown);
          const filename = `${resData.slug}/${resData.filename}`;

          chrome.downloads.download({
            url: blobUrl,
            filename: filename,
            saveAs: true
          }, (downloadId) => {
            if (chrome.runtime.lastError) {
              showStatus('error', `Download failed: ${chrome.runtime.lastError.message}`, '❌');
            } else {
              // Construct highly descriptive path-helper box with click-to-copy
              const htmlContent = `
                <div style="font-weight: 700; margin-bottom: 4px;">Generation Successful!</div>
                <div style="font-size: 11px; opacity: 0.95; margin-bottom: 6px;">Save the downloaded file exactly to this path:</div>
                <div style="background: rgba(0,0,0,0.4); padding: 6px; border-radius: 4px; font-family: monospace; font-size: 11px; word-break: break-all; border: 1px solid rgba(255,255,255,0.15); margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                  <span style="color: #a8ff35; font-weight: 500;">${targetPath}</span>
                  <button id="btn-copy-path" style="background: #ffffff; border: none; color: #000000; padding: 2px 8px; border-radius: 3px; cursor: pointer; font-size: 10px; font-family: var(--font-family); font-weight: 700; flex-shrink: 0; transition: all 0.2s;">COPY</button>
                </div>
              `;
              showStatus('success', htmlContent, '🚀');
              
              // Bind click event to copy path button
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

  // DOM content extraction script (runs in the context of the active tab)
  function extractPageContent() {
    // A. Check for user highlighted text selection first
    const selection = window.getSelection().toString().trim();
    if (selection) {
      return { type: 'selection', title: document.title, content: selection };
    }

    const url = window.location.href;
    const isTwitter = url.includes('x.com') || url.includes('twitter.com');

    if (isTwitter) {
      // Extract author handle from URL
      const urlParts = url.split('/');
      const statusIndex = urlParts.indexOf('status');
      let authorHandle = '';
      if (statusIndex > 1) {
        authorHandle = urlParts[statusIndex - 1].toLowerCase();
      }

      // Select all tweet articles visible on the page
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
              // Grab tweets by the status author, or any tweet if author couldn't be extracted
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

    // B. General fallback: extract title and main reader content
    const container = document.querySelector('article') || document.querySelector('main') || document.body;
    
    // Clone and sanitize content to avoid extra noise
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = container.innerHTML;
    const scripts = tempDiv.querySelectorAll('script, style, nav, footer, header, noscript, iframe');
    scripts.forEach(s => s.remove());
    
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
});
