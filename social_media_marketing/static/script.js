// DOM Elements
let chatMessages, messageInput, sendBtn;
let modeRadios, trendParamsDiv, marketingParamsDiv;

// State
let isProcessing = false;
let sessionId = null;
let userId = null;
let currentMode = 'trend_researcher';

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async function () {
    console.log('DOM loaded, initializing...');

    // Get or create session IDs
    await initializeSession();

    // Get DOM elements
    chatMessages = document.getElementById('chatMessages');
    messageInput = document.getElementById('messageInput');
    sendBtn = document.getElementById('sendBtn');
    modeRadios = document.querySelectorAll('input[name="mode"]');
    trendParamsDiv = document.getElementById('trend-params');
    marketingParamsDiv = document.getElementById('marketing-params');

    // Add event listeners
    if (sendBtn) {
        sendBtn.addEventListener('click', handleSendMessage);
        console.log('Send button listener added');
    }

    if (messageInput) {
        messageInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSendMessage();
            }
        });
    }

    // Mode switching
    modeRadios.forEach(radio => {
        radio.addEventListener('change', function (e) {
            currentMode = e.target.value;
            updateParameterDisplay();
            console.log('Mode changed to:', currentMode);
        });
    });

    // Load message history
    await loadHistory();

    console.log('✅ Initialization complete');
});

/**
 * Update parameter display based on selected mode
 */
function updateParameterDisplay() {
    if (currentMode === 'trend_researcher') {
        trendParamsDiv.classList.add('active');
        marketingParamsDiv.classList.remove('active');
    } else {
        marketingParamsDiv.classList.add('active');
        trendParamsDiv.classList.remove('active');
    }
}

/**
 * Initialize or restore session from localStorage
 */
async function initializeSession() {
    // Try to get from localStorage
    sessionId = localStorage.getItem('sessionId');
    userId = localStorage.getItem('userId');

    // If not found, create new ones
    if (!sessionId || !userId) {
        sessionId = generateUUID();
        userId = generateUUID();

        console.log('📝 Created new session:', { sessionId, userId });

        // Save to localStorage
        localStorage.setItem('sessionId', sessionId);
        localStorage.setItem('userId', userId);

        // Register the session with the server
        try {
            const response = await fetch(`/apps/social_media_marketing/users/${userId}/sessions/${sessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const result = await response.json();
            if (result.success) {
                console.log('✅ Session registered with server');
            } else {
                console.warn('⚠️ Session registration response:', result);
            }
        } catch (error) {
            console.error('❌ Failed to register session:', error);
        }
    } else {
        console.log('📖 Restored session from localStorage:', { sessionId, userId });
    }
}

/**
 * Generate a UUID v4
 */
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0,
            v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/**
 * Load message history from session
 */
async function loadHistory() {
    if (!sessionId || !userId) {
        console.warn('⚠️ Session not initialized, cannot load history');
        return;
    }

    try {
        console.log('📜 Loading message history...');
        const response = await fetch(`/apps/social_media_marketing/users/${userId}/sessions/${sessionId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (result.events?.length > 0) {
            console.log('✅ Loaded', result.events.length, 'messages from history');

            clearWelcomeMessage()

            // Restore messages to chat (trim messages that were constructed by this UI)
            result.events.forEach(event => {
                const role = event.content.role || 'system';
                const texts = event.content.parts.map((part) => part.text || '');
                const raw = texts.join('\n');

                let display = raw;
                if (role === 'user') {
                    display = extractOriginalUserInput(raw);
                }

                addMessage(display, role === 'user' ? 'user' : 'system', false);
            });
        } else {
            console.log('📋 No previous history found, starting fresh');
        }
    } catch (error) {
        console.error('❌ Failed to load history:', error);
    }
}

/**
 * Try to extract the original user input from a message constructed by this UI.
 * Looks for the "User Query:" marker and returns the following content (first paragraph).
 */
function extractOriginalUserInput(raw) {
    if (!raw) return '';

    // Remove leading mode header if present
    raw = raw.replace(/^\s*\[.*?MODE\]\s*/i, '').trim();

    // Find 'User Query:' marker
    const m = raw.match(/User Query:\s*([\s\S]*?)(?:\n\n|$)/i);
    if (m && m[1]) {
        const paragraph = m[1].trim();
        const firstLine = paragraph.split('\n').map(s => s.trim()).filter(Boolean)[0];
        return firstLine || paragraph;
    }

    // Fallback: strip common parameter labels
    return raw.replace(/\n?(Platform:.*|Region:.*|Category:.*|Budget:.*|Duration:.*)/gi, '').trim();
}

/**
 * Build query message with parameters and user input
 */
function buildQueryMessage(userInput) {
    let message = userInput;

    if (currentMode === 'trend_researcher') {
        const platform = document.getElementById('trendPlatform')?.value || '';
        const region = document.getElementById('trendRegion')?.value || '';
        const category = document.getElementById('trendCategory')?.value || '';

        message = `[TREND RESEARCHER MODE]

User Query: ${userInput}

${platform ? `Platform: ${platform}` : ''}
${region ? `Region: ${region}` : ''}
${category ? `Category: ${category}` : ''}

Please analyze social media trends based on this request. Provide trending topics, top creators, audience insights, and recommendations.`;

    } else if (currentMode === 'marketing_advisor') {
        const region = document.getElementById('marketingRegion')?.value || '';
        const budget = document.getElementById('marketingBudget')?.value || '';
        const duration = document.getElementById('marketingDuration')?.value || '';

        message = `[MARKETING ADVISOR MODE]

User Query: ${userInput}

${region ? `Region: ${region}` : ''}
${budget ? `Budget: ${budget} USD` : ''}
${duration ? `Duration: ${duration}` : ''}

Please provide marketing strategy advice and recommendations based on this request.`;
    }

    return message;
}

  /**
   * Parse and validate marketing budget input.
   * Budget can be empty or a valid number >= 0.
   */
  function validateMarketingBudget(value) {
    const raw = String(value || '').trim();

    if (!raw) {
      return { valid: true, normalized: '' };
    }

    const normalized = raw.replace(/,/g, '');
    const numberPattern = /^\d+(?:\.\d+)?$/;

    if (!numberPattern.test(normalized)) {
      return { valid: false, message: 'Budget must be empty or a valid number (e.g., 5000, 5000.50).' };
    }

    const amount = Number(normalized);
    if (!Number.isFinite(amount) || amount < 0) {
      return { valid: false, message: 'Budget must be greater than or equal to 0.' };
    }

    return { valid: true, normalized };
  }

  /**
   * Validate marketing duration input.
   * Accepts values like "3 months", "90 days", "1 year".
   */
  function validateMarketingDuration(value) {
    const raw = String(value || '').trim();
    const durationPattern = /^(\d+(?:\.\d+)?)\s*(day|days|week|weeks|month|months|year|years)$/i;

    if (!durationPattern.test(raw)) {
      return { valid: false, message: 'Duration must be in a valid format like "3 months", "90 days", or "1 year".' };
    }

    const numericValue = Number(raw.match(durationPattern)[1]);
    if (!Number.isFinite(numericValue) || numericValue <= 0) {
      return { valid: false, message: 'Duration value must be greater than 0.' };
    }

    return { valid: true };
  }

/**
 * Handle sending message
 */
async function handleSendMessage() {
    if (isProcessing) {
        console.log('⏳ Already processing...');
        return;
    }

    const userInput = messageInput.value.trim();
    if (!userInput) {
        return;
    }

    if (currentMode === 'marketing_advisor') {
      const marketingBudgetInput = document.getElementById('marketingBudget');
      const marketingDurationInput = document.getElementById('marketingDuration');

      const budgetValidation = validateMarketingBudget(marketingBudgetInput?.value || '');
      if (!budgetValidation.valid) {
        addMessage(`❌ Validation Error: ${budgetValidation.message}`, 'error');
        marketingBudgetInput?.focus();
        return;
      }

      const durationValue = (marketingDurationInput?.value || '').trim();
      if (!durationValue) {
        addMessage('❌ Validation Error: Duration is required and must be in a format like "3 months", "90 days", or "1 year".', 'error');
        marketingDurationInput?.focus();
        return;
      }

      const durationValidation = validateMarketingDuration(durationValue);
      if (!durationValidation.valid) {
        addMessage(`❌ Validation Error: ${durationValidation.message}`, 'error');
        marketingDurationInput?.focus();
        return;
      }
    }

    // Check API key
    try {
        const healthCheck = await fetch('/api/health');
        const health = await healthCheck.json();

        if (!health.api_key_configured) {
            addMessage('❌ Error: GOOGLE_API_KEY not configured. Please add your API key to the .env file.', 'error');
            return;
        }
    } catch (e) {
        console.error('Health check failed:', e);
    }

    isProcessing = true;
    sendBtn.disabled = true;
    messageInput.disabled = true;

    clearWelcomeMessage();

    // Add user message to chat
    addMessage(userInput, 'user');

    // Clear input
    messageInput.value = '';

    // Show loading indicator
    showLoading('Processing your request...');

    try {
        // Build query message with parameters
        const queryMessage = buildQueryMessage(userInput);

        console.log('📤 Sending message:', queryMessage);

        // Send to /run endpoint
        const response = await fetch('/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                app_name: 'social_media_marketing',
                sessionId: sessionId,
                userId: userId,
                newMessage: { 
                    role: "user", 
                    parts: [{ text: queryMessage }] 
                }
            })
        });

        clearLoading();

        if (response.status === 200) {
            const data = await response.json();

            let message = '';

            data.forEach((item) => {
                if (item.content?.parts) {
                    const texts = item.content.parts.map((part) => part.text || '');
                    message += texts.join(' ');
                }
            });

            addMessage(message, 'system');
        } else {
            const err = await response.json().catch(() => ({}));
            const errorMsg = err.error || 'Analysis failed. Please try again.';
            addMessage(`❌ Error: ${errorMsg}`, 'error');
        }

    } catch (error) {
        clearLoading();
        console.error('Error:', error);
        addMessage(`❌ Error processing request: ${error.message}`, 'error');
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        messageInput.disabled = false;
        messageInput.focus();
    }
}

/**
 * Add message to chat
 */
function addMessage(text, type = 'system', scroll = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;

    let icon = '🤖';
    if (type === 'error') {
        icon = '❌';
    } else if (type === 'user') {
        icon = '👤';
    }

    // Render message content with simple markdown-like handling so tables/lists/headings are preserved
    // const html = renderMessageContent(text || '');
    const html = renderSocialMediaContent(text || '')

    messageDiv.innerHTML = `
        <div class="message-icon">${icon}</div>
        <div class="message-content">
            ${html}
            <span class="message-time">${new Date().toLocaleTimeString()}</span>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    if (scroll) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function renderSocialMediaContent(markdownContent, options = {}) {
  const {
    className = 'social-media-table',
    striped = true,
    bordered = true,
    responsive = true,
    containerClass = 'social-media-output'
  } = options;

  // Split content into blocks
  const blocks = parseContentBlocks(markdownContent);
  
  let html = `<div class="${containerClass}">`;
  
  blocks.forEach(block => {
    switch (block.type) {
      case 'table':
        html += renderTable(block.content, { className, striped, bordered, responsive });
        break;
      case 'heading':
        html += renderHeading(block.content, block.level);
        break;
      case 'paragraph':
        html += renderParagraph(block.content);
        break;
      case 'list':
        html += renderList(block.content, block.ordered);
        break;
      default:
        html += `<p>${escapeHtml(block.content)}</p>`;
    }
  });
  
  html += '</div>';
  
  return html;
}

/**
 * Parses markdown content into structured blocks
 */
function parseContentBlocks(content) {
  const lines = content.split('\n');
  const blocks = [];
  let tableLines = [];
  let listLines = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // Detect table start (line with |)
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      // If we were building a list, finalize it
      if (listLines.length > 0) {
        blocks.push(createListBlock(listLines));
        listLines = [];
      }
      
      tableLines = [line];
      i++;
      
      // Collect all table lines
      while (i < lines.length && lines[i].trim().includes('|')) {
        tableLines.push(lines[i]);
        i++;
      }
      
      blocks.push({
        type: 'table',
        content: tableLines.join('\n')
      });
      continue;
    }
    
    // Detect headings (### or ##)
    if (trimmed.startsWith('#')) {
      // Finalize any ongoing list
      if (listLines.length > 0) {
        blocks.push(createListBlock(listLines));
        listLines = [];
      }
      
      const level = trimmed.match(/^#+/)[0].length;
      const text = trimmed.replace(/^#+\s*/, '').trim();
      blocks.push({
        type: 'heading',
        level: level,
        content: text
      });
      i++;
      continue;
    }
    
    // Detect lists (lines starting with * or - or numbered)
    if (trimmed.match(/^[\*\-]\s+/) || trimmed.match(/^\d+\.\s+/)) {
      const isOrdered = trimmed.match(/^\d+\.\s+/) !== null;
      listLines.push({
        text: trimmed.replace(/^[\*\-]\s+/, '').replace(/^\d+\.\s+/, ''),
        ordered: isOrdered
      });
      i++;
      continue;
    }
    
    // If we were building a list and hit non-list content, finalize the list
    if (listLines.length > 0 && !trimmed.match(/^[\*\-]\s+/) && !trimmed.match(/^\d+\.\s+/)) {
      blocks.push(createListBlock(listLines));
      listLines = [];
    }
    
    // Regular paragraph
    if (trimmed.length > 0) {
      blocks.push({
        type: 'paragraph',
        content: trimmed
      });
    }
    
    i++;
  }
  
  // Finalize any remaining list
  if (listLines.length > 0) {
    blocks.push(createListBlock(listLines));
  }
  
  return blocks;
}

/**
 * Creates a list block from collected list lines
 */
function createListBlock(listLines) {
  const isOrdered = listLines.some(item => item.ordered);
  return {
    type: 'list',
    ordered: isOrdered,
    content: listLines.map(item => item.text)
  };
}

/**
 * Renders a markdown table into HTML
 */
function renderTable(markdownTable, options) {
  const { className, striped, bordered, responsive } = options;
  
  const lines = markdownTable.split('\n').filter(line => line.trim());
  
  if (lines.length < 2) {
    return '<p class="error">Invalid table format</p>';
  }

  // Parse header row
  const headers = lines[0]
    .split('|')
    .map(h => h.trim())
    .filter(h => h);

  // Skip separator line (line with :----)
  const dataRows = lines.slice(2);

  // Parse data rows
  const rows = dataRows.map(line => {
    return line
      .split('|')
      .map(cell => cell.trim())
      .filter(cell => cell);
  });

  // Generate HTML
  let html = responsive ? '<div class="table-responsive">' : '';
  
  html += `<table class="${className}${striped ? ' table-striped' : ''}${bordered ? ' table-bordered' : ''}">`;
  
  // Table header
  html += '<thead><tr>';
  headers.forEach(header => {
    html += `<th>${escapeHtml(header)}</th>`;
  });
  html += '</tr></thead>';
  
  // Table body
  html += '<tbody>';
  rows.forEach(row => {
    html += '<tr>';
    row.forEach((cell, index) => {
      let formattedCell = formatCellContent(cell, headers[index]);
      html += `<td>${formattedCell}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody></table>';
  
  html += responsive ? '</div>' : '';
  
  return html;
}

/**
 * Renders a heading element
 */
function renderHeading(text, level) {
  const sanitized = escapeHtml(text);
  const headingLevel = Math.min(Math.max(level, 1), 6); // Clamp between 1-6
  return `<h${headingLevel}>${sanitized}</h${headingLevel}>`;
}

/**
 * Renders a paragraph with inline formatting
 */
function renderParagraph(text) {
  let formatted = escapeHtml(text);
  
  // Bold (**text** or __text__)
  formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/__(.+?)__/g, '<strong>$1</strong>');
  
  // Italic (*text* or _text_)
  formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>');
  formatted = formatted.replace(/_(.+?)_/g, '<em>$1</em>');
  
  // Code (`text`)
  formatted = formatted.replace(/`(.+?)`/g, '<code>$1</code>');
  
  return `<p>${formatted}</p>`;
}

/**
 * Renders a list (ordered or unordered)
 */
function renderList(items, ordered = false) {
  const tag = ordered ? 'ol' : 'ul';
  let html = `<${tag}>`;
  
  items.forEach(item => {
    let formatted = escapeHtml(item);
    
    // Apply inline formatting
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/`(.+?)`/g, '<code>$1</code>');
    
    html += `<li>${formatted}</li>`;
  });
  
  html += `</${tag}>`;
  return html;
}

/**
 * Formats cell content based on column type and special markers
 */
function formatCellContent(cell, headerName = '') {
  let formatted = escapeHtml(cell);
  
  // Handle star ratings - convert to visual stars
  if (formatted.includes('⭐')) {
    const starCount = (formatted.match(/⭐/g) || []).length;
    const maxStars = 5;
    formatted = `<span class="star-rating" data-rating="${starCount}">`;
    for (let i = 0; i < maxStars; i++) {
      formatted += i < starCount 
        ? '<span class="star filled">⭐</span>' 
        : '<span class="star empty">☆</span>';
    }
    formatted += `</span>`;
  }
  
  // Handle N/A values
  if (formatted === 'N/A') {
    formatted = '<span class="text-muted">N/A</span>';
  }
  
  // Handle engagement tiers with badges
  if (headerName && headerName.includes('Engagement Tier')) {
    const tierMatch = formatted.match(/(Nano|Micro|Mid|Macro|Mega|Viral Trend|Emerging|General Trend)/i);
    if (tierMatch) {
      const tier = tierMatch[1];
      formatted = `<span class="badge tier-${tier.toLowerCase().replace(/\s+/g, '-')}">${escapeHtml(formatted)}</span>`;
    }
  }
  
  // Handle follower counts - add formatting
  if (headerName && headerName.includes('Followers')) {
    formatted = `<span class="follower-count">${formatted}</span>`;
  }
  
  // Handle creator names/handles - make them stand out
  if (headerName && headerName.includes('Creator Name')) {
    if (formatted.includes('@')) {
      formatted = formatted.replace(
        /(@[\w_]+)/g, 
        '<span class="creator-handle">$1</span>'
      );
    }
    formatted = `<strong class="creator-name">${formatted}</strong>`;
  }
  
  // Handle parenthetical notes
  formatted = formatted.replace(
    /\(([^)]+)\)/g, 
    '<span class="note">($1)</span>'
  );
  
  return formatted;
}

/**
 * Escapes HTML special characters to prevent XSS
 */
function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}


/**
 * Show loading indicator
 */
function showLoading(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message system';
    messageDiv.id = 'loading-message';

    messageDiv.innerHTML = `
        <div class="message-icon">⏳</div>
        <div class="message-content">
            <p>${message}</p>
            <div style="margin-top: 10px;">
                <span class="loading"></span>
                <span class="loading"></span>
                <span class="loading"></span>
            </div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Clear loading indicator
 */
function clearLoading() {
    const loadingMsg = document.getElementById('loading-message');
    if (loadingMsg) {
        loadingMsg.remove();
    }
}

function clearWelcomeMessage() {
    const welcomeMsg = document.getElementById('welcomeMessage');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
}