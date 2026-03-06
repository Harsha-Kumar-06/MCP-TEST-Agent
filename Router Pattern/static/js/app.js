/**
 * CorpAssist - Chat Application JavaScript
 */

// State
let sessionId = null;
let isLoading = false;
let escalationId = null;
let escalationWebSocket = null;
let isEscalated = false;
let userTimezone = null;

// Inactivity tracking for live chat
let lastActivityTime = null;
let inactivityTimer = null;
let pendingNewChat = false;
const INACTIVITY_TIMEOUT = 2 * 60 * 1000; // 2 minutes

// Chat session management
let currentChatSessionId = null;
const CHAT_SESSIONS_KEY = 'corpassist_chat_sessions';
const CURRENT_SESSION_KEY = 'corpassist_current_session';

// Agent conversation memory state
let agentConversations = {}; // {agent_name: [{role, content, timestamp}]}
let currentAgent = null; // Track which agent we're currently viewing
let lastRoutedAgent = null; // Track the last agent that responded

// DOM Elements
const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const loadingOverlay = document.getElementById('loadingOverlay');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initSession();
    autoResizeTextarea();
    detectUserTimezone();
});

// Detect user's timezone
function detectUserTimezone() {
    try {
        userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        console.log('Detected user timezone:', userTimezone);
    } catch (e) {
        console.error('Failed to detect timezone:', e);
        userTimezone = 'UTC';
    }
}

// Get current date/time info for the user
function getCurrentTimeInfo() {
    const now = new Date();
    return {
        timezone: userTimezone,
        localTime: now.toLocaleTimeString(),
        localDate: now.toLocaleDateString(),
        dayOfWeek: now.toLocaleDateString('en-US', { weekday: 'long' }),
        isoTime: now.toISOString()
    };
}

// Initialize session
async function initSession() {
    try {
        // Check if we have a stored session ID
        const storedSessionId = localStorage.getItem('corpassist_session_id');
        
        if (storedSessionId) {
            sessionId = storedSessionId;
            console.log('Restored session:', sessionId);
        } else {
            const response = await fetch('/api/session/new', { method: 'POST' });
            const data = await response.json();
            sessionId = data.session_id;
            localStorage.setItem('corpassist_session_id', sessionId);
            console.log('Session initialized:', sessionId);
        }
        
        // Initialize agent conversations
        agentConversations = {};
        currentAgent = null;
        lastRoutedAgent = null;
        
        // Initialize or restore chat session
        initChatSession();
        
        // Check for active escalation and restore if exists
        await restoreEscalationState();
        
    } catch (error) {
        console.error('Failed to initialize session:', error);
    }
}

// Save escalation state to localStorage
function saveEscalationState(escId) {
    if (escId) {
        localStorage.setItem('corpassist_escalation_id', escId);
        localStorage.setItem('corpassist_escalation_time', Date.now().toString());
        console.log('Escalation state saved:', escId);
    }
}

// Clear escalation state from localStorage
function clearEscalationState() {
    localStorage.removeItem('corpassist_escalation_id');
    localStorage.removeItem('corpassist_escalation_time');
    localStorage.removeItem('corpassist_chat_history');
    console.log('Escalation state cleared');
}

// Save chat history to localStorage (backup for page refresh)
function saveChatHistoryToLocal(escId, messages) {
    if (escId && messages) {
        try {
            const data = { escalation_id: escId, messages: messages, saved_at: Date.now() };
            localStorage.setItem('corpassist_chat_history', JSON.stringify(data));
        } catch (e) {
            console.error('Failed to save chat history to localStorage:', e);
        }
    }
}

// Load chat history from localStorage (fallback when server unavailable)
function loadLocalChatHistory() {
    try {
        const data = localStorage.getItem('corpassist_chat_history');
        if (data) {
            return JSON.parse(data);
        }
    } catch (e) {
        console.error('Failed to load local chat history:', e);
    }
    return null;
}

// Append a message to local chat history backup
function appendToLocalHistory(message) {
    if (!escalationId) return;
    
    try {
        let data = loadLocalChatHistory();
        if (!data || data.escalation_id !== escalationId) {
            data = { escalation_id: escalationId, messages: [], saved_at: Date.now() };
        }
        data.messages.push(message);
        data.saved_at = Date.now();
        localStorage.setItem('corpassist_chat_history', JSON.stringify(data));
    } catch (e) {
        console.error('Failed to append to local history:', e);
    }
}

// ========== FULL CHAT HISTORY PERSISTENCE ==========

// Save all chat messages to localStorage
function saveAllChatHistory() {
    try {
        const messages = [];
        document.querySelectorAll('.message').forEach(msgEl => {
            const content = msgEl.querySelector('.message-content');
            if (!content) return;
            
            // Get the text content without the meta time
            const textNodes = content.cloneNode(true);
            const metaEl = textNodes.querySelector('.message-meta');
            const routedBadge = textNodes.querySelector('.routed-badge');
            if (metaEl) metaEl.remove();
            if (routedBadge) routedBadge.remove();
            
            let role = 'assistant';
            if (msgEl.classList.contains('user')) role = 'user';
            else if (msgEl.classList.contains('specialist')) role = 'specialist';
            else if (msgEl.classList.contains('system')) role = 'system';
            
            // Get routed agent from badge if exists
            let routedTo = null;
            const badge = content.querySelector('.routed-badge');
            if (badge) {
                const badgeText = badge.textContent.trim();
                // Map display names back to agent names
                const agentMap = {
                    'HR Support': 'hr_agent',
                    'IT Support': 'it_support_agent',
                    'Sales Support': 'sales_agent',
                    'Legal Support': 'legal_agent',
                    'General': 'off_topic_agent',
                    'Human Specialist': 'Human Specialist'
                };
                for (const [display, agent] of Object.entries(agentMap)) {
                    if (badgeText.includes(display)) {
                        routedTo = agent;
                        break;
                    }
                }
            }
            
            messages.push({
                role: role,
                content: textNodes.innerHTML,
                routedTo: routedTo,
                timestamp: Date.now()
            });
        });
        
        const data = {
            session_id: sessionId,
            messages: messages,
            saved_at: Date.now()
        };
        localStorage.setItem('corpassist_full_chat_history', JSON.stringify(data));
    } catch (e) {
        console.error('Failed to save full chat history:', e);
    }
}

// Load all chat history from localStorage
function loadAllChatHistory() {
    try {
        const data = localStorage.getItem('corpassist_full_chat_history');
        if (data) {
            return JSON.parse(data);
        }
    } catch (e) {
        console.error('Failed to load full chat history:', e);
    }
    return null;
}

// Restore chat history on page load
function restoreChatHistory() {
    const data = loadAllChatHistory();
    if (!data || !data.messages || data.messages.length === 0) {
        return false;
    }
    
    // Check if session matches or if it's recent enough (24 hours)
    const maxAge = 24 * 60 * 60 * 1000;
    if (data.saved_at && (Date.now() - data.saved_at) > maxAge) {
        // Too old, clear it
        localStorage.removeItem('corpassist_full_chat_history');
        return false;
    }
    
    console.log('Restoring chat history:', data.messages.length, 'messages');
    hideWelcome();
    
    data.messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.role}`;
        
        let avatar;
        if (msg.role === 'assistant') {
            avatar = '<i class="fas fa-robot"></i>';
        } else if (msg.role === 'specialist') {
            avatar = '<i class="fas fa-headset"></i>';
        } else if (msg.role === 'system') {
            avatar = '<i class="fas fa-info-circle"></i>';
        } else {
            avatar = '<i class="fas fa-user"></i>';
        }
        
        let routedBadge = '';
        if (msg.routedTo && (msg.role === 'assistant' || msg.role === 'specialist')) {
            const agentNames = {
                'hr_agent': 'HR Support',
                'it_support_agent': 'IT Support',
                'sales_agent': 'Sales Support',
                'legal_agent': 'Legal Support',
                'off_topic_agent': 'General',
                'Human Specialist': 'Human Specialist'
            };
            const displayName = agentNames[msg.routedTo] || msg.routedTo;
            const icon = msg.role === 'specialist' ? 'fa-headset' : 'fa-route';
            routedBadge = `<div class="routed-badge"><i class="fas ${icon}"></i> ${displayName}</div>`;
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                ${msg.content}
                ${routedBadge}
                <div class="message-meta">Restored</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
    });
    
    scrollToBottom();
    return true;
}

// Clear all chat history
function clearAllChatHistory() {
    localStorage.removeItem('corpassist_full_chat_history');
    console.log('Full chat history cleared');
}

// ========== CHAT SESSION MANAGEMENT ==========

// Generate unique session ID
function generateChatSessionId() {
    return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Get all chat sessions from localStorage
function getAllChatSessions() {
    try {
        const data = localStorage.getItem(CHAT_SESSIONS_KEY);
        return data ? JSON.parse(data) : [];
    } catch (e) {
        console.error('Failed to load chat sessions:', e);
        return [];
    }
}

// Save all chat sessions to localStorage
function saveAllChatSessions(sessions) {
    try {
        localStorage.setItem(CHAT_SESSIONS_KEY, JSON.stringify(sessions));
    } catch (e) {
        console.error('Failed to save chat sessions:', e);
    }
}

// Save current chat as a session
function saveCurrentChatSession() {
    const messages = getCurrentChatMessages();
    if (!messages || messages.length === 0) {
        return null;
    }
    
    // Create or update session
    const sessions = getAllChatSessions();
    
    // Get first user message as title preview
    const firstUserMsg = messages.find(m => m.role === 'user');
    const title = firstUserMsg ? firstUserMsg.content.substring(0, 50) : 'New Conversation';
    
    // Get last message for preview
    const lastMsg = messages[messages.length - 1];
    const preview = lastMsg ? lastMsg.content.substring(0, 80) : '';
    
    const sessionData = {
        id: currentChatSessionId || generateChatSessionId(),
        title: title + (title.length >= 50 ? '...' : ''),
        preview: preview + (preview.length >= 80 ? '...' : ''),
        messages: messages,
        messageCount: messages.length,
        createdAt: sessions.find(s => s.id === currentChatSessionId)?.createdAt || Date.now(),
        updatedAt: Date.now()
    };
    
    // Update or add session
    const existingIndex = sessions.findIndex(s => s.id === sessionData.id);
    if (existingIndex >= 0) {
        sessions[existingIndex] = sessionData;
    } else {
        sessions.unshift(sessionData); // Add to beginning
    }
    
    // Keep only last 50 sessions
    if (sessions.length > 50) {
        sessions.splice(50);
    }
    
    saveAllChatSessions(sessions);
    currentChatSessionId = sessionData.id;
    localStorage.setItem(CURRENT_SESSION_KEY, currentChatSessionId);
    
    return sessionData.id;
}

// Get current chat messages from DOM
function getCurrentChatMessages() {
    const messages = [];
    document.querySelectorAll('.message').forEach(msgEl => {
        const content = msgEl.querySelector('.message-content');
        if (!content) return;
        
        // Clone and remove meta elements
        const textNodes = content.cloneNode(true);
        const metaEl = textNodes.querySelector('.message-meta');
        const routedBadge = textNodes.querySelector('.routed-badge');
        if (metaEl) metaEl.remove();
        if (routedBadge) routedBadge.remove();
        
        let role = 'assistant';
        if (msgEl.classList.contains('user')) role = 'user';
        else if (msgEl.classList.contains('specialist')) role = 'specialist';
        else if (msgEl.classList.contains('system-message')) role = 'system';
        
        // Get routed agent
        let routedTo = null;
        const badge = content.querySelector('.routed-badge');
        if (badge) {
            const badgeText = badge.textContent.trim();
            const agentMap = {
                'HR Support': 'hr_agent',
                'IT Support': 'it_support_agent',
                'Sales Support': 'sales_agent',
                'Legal Support': 'legal_agent',
                'General': 'off_topic_agent',
                'Human Specialist': 'Human Specialist'
            };
            for (const [display, agent] of Object.entries(agentMap)) {
                if (badgeText.includes(display)) {
                    routedTo = agent;
                    break;
                }
            }
        }
        
        messages.push({
            role: role,
            content: textNodes.innerHTML,
            routedTo: routedTo,
            timestamp: Date.now()
        });
    });
    
    return messages;
}

// Load a chat session by ID
function loadChatSession(chatSessionId) {
    const sessions = getAllChatSessions();
    const session = sessions.find(s => s.id === chatSessionId);
    
    if (!session || !session.messages || session.messages.length === 0) {
        console.error('Session not found or empty:', chatSessionId);
        return false;
    }
    
    // Clear current chat
    messagesContainer.innerHTML = '';
    hideWelcome();
    
    // Restore messages
    session.messages.forEach(msg => {
        if (msg.role === 'system') {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message system-message';
            msgDiv.innerHTML = `<div class="system-content"><i class="fas fa-info-circle"></i> ${msg.content}</div>`;
            messagesContainer.appendChild(msgDiv);
        } else {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${msg.role}`;
            
            let avatar;
            if (msg.role === 'assistant') avatar = '<i class="fas fa-robot"></i>';
            else if (msg.role === 'specialist') avatar = '<i class="fas fa-headset"></i>';
            else avatar = '<i class="fas fa-user"></i>';
            
            let routedBadge = '';
            if (msg.routedTo && (msg.role === 'assistant' || msg.role === 'specialist')) {
                const agentNames = {
                    'hr_agent': 'HR Support',
                    'it_support_agent': 'IT Support',
                    'sales_agent': 'Sales Support',
                    'legal_agent': 'Legal Support',
                    'off_topic_agent': 'General',
                    'Human Specialist': 'Human Specialist'
                };
                const displayName = agentNames[msg.routedTo] || msg.routedTo;
                const icon = msg.role === 'specialist' ? 'fa-headset' : 'fa-route';
                routedBadge = `<div class="routed-badge"><i class="fas ${icon}"></i> ${displayName}</div>`;
            }
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    ${msg.content}
                    ${routedBadge}
                    <div class="message-meta">Restored</div>
                </div>
            `;
            messagesContainer.appendChild(messageDiv);
        }
    });
    
    scrollToBottom();
    currentChatSessionId = chatSessionId;
    localStorage.setItem(CURRENT_SESSION_KEY, chatSessionId);
    
    // Close history panel
    toggleChatHistory();
    
    console.log('Loaded chat session:', chatSessionId);
    return true;
}

// Delete a chat session
function deleteChatSession(chatSessionId, event) {
    if (event) event.stopPropagation();
    
    if (!confirm('Delete this conversation?')) return;
    
    const sessions = getAllChatSessions();
    const filtered = sessions.filter(s => s.id !== chatSessionId);
    saveAllChatSessions(filtered);
    
    // If we deleted the current session, clear the chat
    if (chatSessionId === currentChatSessionId) {
        currentChatSessionId = null;
        localStorage.removeItem(CURRENT_SESSION_KEY);
        messagesContainer.innerHTML = '';
        showWelcome();
    }
    
    // Refresh the history panel
    renderChatHistoryPanel();
}

// Clear all chat sessions
function clearAllSessions() {
    if (!confirm('Delete ALL chat history? This cannot be undone.')) return;
    
    localStorage.removeItem(CHAT_SESSIONS_KEY);
    localStorage.removeItem(CURRENT_SESSION_KEY);
    currentChatSessionId = null;
    
    messagesContainer.innerHTML = '';
    showWelcome();
    
    renderChatHistoryPanel();
    addSystemMessage('All chat history has been cleared.');
}

// Toggle chat history panel
function toggleChatHistory() {
    const panel = document.getElementById('chatHistoryPanel');
    if (panel) {
        panel.classList.toggle('open');
        if (panel.classList.contains('open')) {
            renderChatHistoryPanel();
        }
    }
}

// Render chat history panel
function renderChatHistoryPanel() {
    const content = document.getElementById('historyPanelContent');
    if (!content) return;
    
    const sessions = getAllChatSessions();
    
    if (sessions.length === 0) {
        content.innerHTML = `
            <div class="no-history-message">
                <i class="fas fa-comments"></i>
                <p>No chat history yet</p>
                <p style="font-size: 0.8rem;">Your conversations will appear here</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    sessions.forEach(session => {
        const date = new Date(session.updatedAt);
        const dateStr = date.toLocaleDateString();
        const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const isActive = session.id === currentChatSessionId;
        
        // Strip HTML tags for display
        const cleanTitle = session.title.replace(/<[^>]*>/g, '').substring(0, 40);
        const cleanPreview = session.preview.replace(/<[^>]*>/g, '').substring(0, 60);
        
        html += `
            <div class="history-session-item ${isActive ? 'active' : ''}" onclick="loadChatSession('${session.id}')">
                <div class="session-title">
                    <span>${cleanTitle}${cleanTitle.length >= 40 ? '...' : ''}</span>
                    ${isActive ? '<i class="fas fa-check-circle" style="color: var(--primary-color);"></i>' : ''}
                </div>
                <div class="session-preview">${cleanPreview}${cleanPreview.length >= 60 ? '...' : ''}</div>
                <div class="session-meta">
                    <span><i class="fas fa-comment"></i> ${session.messageCount} messages</span>
                    <span>${dateStr} ${timeStr}</span>
                </div>
                <button class="session-delete-btn" onclick="deleteChatSession('${session.id}', event)">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        `;
    });
    
    content.innerHTML = html;
}

// Initialize or restore chat session on page load
function initChatSession() {
    const savedSessionId = localStorage.getItem(CURRENT_SESSION_KEY);
    if (savedSessionId) {
        const sessions = getAllChatSessions();
        const session = sessions.find(s => s.id === savedSessionId);
        if (session) {
            currentChatSessionId = savedSessionId;
            loadChatSession(savedSessionId);
            return true;
        }
    }
    
    // No session to restore, create new one
    currentChatSessionId = generateChatSessionId();
    localStorage.setItem(CURRENT_SESSION_KEY, currentChatSessionId);
    return false;
}

// Restore escalation state after page refresh
async function restoreEscalationState() {
    const storedEscalationId = localStorage.getItem('corpassist_escalation_id');
    const storedTime = localStorage.getItem('corpassist_escalation_time');
    
    if (!storedEscalationId) {
        return;
    }
    
    console.log('Found stored escalation:', storedEscalationId);
    
    // Check if escalation is too old (24 hours)
    const maxAge = 24 * 60 * 60 * 1000; // 24 hours
    const isExpired = storedTime && (Date.now() - parseInt(storedTime)) > maxAge;
    
    // Check escalation status on server
    try {
        const response = await fetch(`/api/escalation/${storedEscalationId}/status`);
        
        if (response.ok) {
            const data = await response.json();
            
            // Always load chat history first
            await loadEscalationHistory(storedEscalationId);
            
            if (data.status === 'closed' || data.status === 'resolved' || isExpired) {
                // Session ended - show history in read-only mode
                console.log('Escalation session ended, showing history');
                const reason = isExpired ? 'expired' : data.status;
                addSystemMessage(`Previous chat session (${reason}). You can ask the AI assistant to connect you with a specialist if you need more help.`);
                showChatEndedState();
            } else {
                // Active session - reconnect
                console.log('Restoring active escalation:', storedEscalationId);
                escalationId = storedEscalationId;
                isEscalated = true;
                addSystemMessage(`Reconnecting to live chat session...`);
                connectEscalationWebSocket(storedEscalationId);
            }
            
        } else if (response.status === 404) {
            // Escalation not found on server - try to load local history
            console.log('Escalation not found on server, checking localStorage...');
            const loaded = await loadEscalationHistory(storedEscalationId);
            if (loaded) {
                addSystemMessage(`Previous session no longer active on server. History shown from local backup.`);
            } else {
                addSystemMessage(`Previous session not found.`);
            }
            showChatEndedState();
        }
    } catch (error) {
        console.error('Failed to check escalation status:', error);
        // Network error - try to load history from localStorage and attempt reconnect
        const loaded = await loadEscalationHistory(storedEscalationId);
        if (loaded) {
            escalationId = storedEscalationId;
            isEscalated = true;
            addSystemMessage(`Network issue detected. Attempting to reconnect...`);
            connectEscalationWebSocket(storedEscalationId);
        } else {
            addSystemMessage(`Unable to restore previous session. Please start a new chat.`);
            showChatEndedState();
        }
    }
}

// Show chat ended state (read-only mode)
function showChatEndedState() {
    isEscalated = false;
    escalationId = null;
    
    // Disable input with message
    const inputContainer = document.querySelector('.input-container');
    if (inputContainer && !document.getElementById('chatEndedBanner')) {
        const banner = document.createElement('div');
        banner.id = 'chatEndedBanner';
        banner.className = 'chat-ended-banner';
        banner.innerHTML = `
            <i class="fas fa-history"></i>
            <span>This chat session has ended. </span>
            <button onclick="startNewChat()" class="new-chat-inline-btn">Start New Chat</button>
        `;
        inputContainer.parentNode.insertBefore(banner, inputContainer);
    }
}

// Load escalation chat history from server
async function loadEscalationHistory(escId) {
    try {
        const response = await fetch(`/api/escalation/${escId}/history`);
        if (response.ok) {
            const data = await response.json();
            
            // Save to localStorage as backup
            saveChatHistoryToLocal(escId, data.messages);
            
            // Hide welcome message
            hideWelcome();
            
            // Display chat history
            if (data.messages && data.messages.length > 0) {
                displayChatMessages(data.messages);
            }
            return true;
        }
    } catch (error) {
        console.error('Failed to load escalation history from server:', error);
    }
    
    // Fallback to localStorage if server unavailable
    const localHistory = loadLocalChatHistory();
    if (localHistory && localHistory.escalation_id === escId) {
        console.log('Loading chat history from localStorage backup');
        hideWelcome();
        if (localHistory.messages && localHistory.messages.length > 0) {
            displayChatMessages(localHistory.messages);
            addSystemMessage('Chat history loaded from local backup. Some recent messages may be missing.');
        }
        return true;
    }
    
    return false;
}

// Display chat messages from history
function displayChatMessages(messages) {
    messages.forEach(msg => {
        if (msg.role === 'user') {
            addMessageWithoutScroll(msg.content, 'user');
        } else if (msg.role === 'specialist') {
            addMessageWithoutScroll(msg.content, 'specialist', 'Human Specialist');
        } else if (msg.role === 'ai' || msg.role === 'assistant') {
            addMessageWithoutScroll(msg.content, 'assistant', 'AI Assistant');
        } else if (msg.role === 'system') {
            // Add system message inline
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message system-message';
            msgDiv.innerHTML = `<div class="system-content"><i class="fas fa-info-circle"></i> ${msg.content}</div>`;
            messagesContainer.appendChild(msgDiv);
        }
    });
    scrollToBottom();
}

// =============================================================================
// Agent Conversation Memory Functions
// =============================================================================

// Agent display names and icons
const agentConfig = {
    'hr_agent': { name: 'HR Support', icon: 'fa-user-tie', color: '#8B5CF6' },
    'it_support_agent': { name: 'IT Support', icon: 'fa-laptop-code', color: '#3B82F6' },
    'sales_agent': { name: 'Sales Support', icon: 'fa-chart-line', color: '#10B981' },
    'legal_agent': { name: 'Legal Support', icon: 'fa-gavel', color: '#F59E0B' },
    'off_topic_agent': { name: 'General', icon: 'fa-comments', color: '#6B7280' },
    'helpdesk_router': { name: 'HelpDesk', icon: 'fa-robot', color: '#4F46E5' }
};

// Fetch agent conversations from server
async function fetchAgentConversations() {
    if (!sessionId) return;
    
    try {
        const response = await fetch(`/api/session/${sessionId}/agents`);
        const data = await response.json();
        
        if (data.agents && data.agents.length > 0) {
            renderAgentTabs(data.agents, data.active_agent);
        }
    } catch (error) {
        console.error('Failed to fetch agent conversations:', error);
    }
}

// Render agent tabs in the UI
function renderAgentTabs(agents, activeAgent) {
    const container = document.getElementById('agentTabsContainer');
    const tabsDiv = document.getElementById('agentTabs');
    
    if (!agents || agents.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    tabsDiv.innerHTML = '';
    
    agents.forEach(agent => {
        const config = agentConfig[agent.agent] || { name: agent.agent, icon: 'fa-robot', color: '#4F46E5' };
        const isActive = agent.agent === currentAgent || (currentAgent === null && agent.agent === activeAgent);
        const hasNew = agent.agent !== currentAgent && agent.agent === lastRoutedAgent && lastRoutedAgent !== currentAgent;
        
        const tab = document.createElement('button');
        tab.className = `agent-tab ${isActive ? 'active' : ''}`;
        tab.setAttribute('data-agent', agent.agent);
        tab.onclick = () => switchToAgent(agent.agent);
        
        tab.innerHTML = `
            <i class="fas ${config.icon} agent-icon"></i>
            <span class="agent-name">${config.name}</span>
            <span class="message-count">${Math.floor(agent.message_count / 2)}</span>
            ${hasNew ? '<span class="new-indicator"></span>' : ''}
        `;
        
        tabsDiv.appendChild(tab);
    });
}

// Switch to a different agent's conversation
async function switchToAgent(agentName) {
    if (agentName === currentAgent) return;
    
    try {
        // First, save current messages to local cache
        saveCurrentMessagesToCache();
        
        const response = await fetch(`/api/session/${sessionId}/agent/${agentName}/switch`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            currentAgent = agentName;
            
            // Clear messages and show the agent's conversation history
            clearMessages();
            displayAgentHistory(data.messages, agentName);
            
            // Update tabs UI
            updateAgentTabsUI();
            
            // Update header to show current agent
            const config = agentConfig[agentName] || { name: agentName };
            addSystemMessage(`Switched to ${config.name} conversation`);
            
        } else {
            console.error('Failed to switch agent:', data.error);
        }
    } catch (error) {
        console.error('Error switching agent:', error);
    }
}

// Save current messages to local cache
function saveCurrentMessagesToCache() {
    if (!currentAgent) return;
    
    const messages = [];
    const messageDivs = messagesContainer.querySelectorAll('.message:not(.system-message)');
    
    messageDivs.forEach(div => {
        const isUser = div.classList.contains('user');
        const content = div.querySelector('.message-content')?.innerText || '';
        if (content) {
            messages.push({
                role: isUser ? 'user' : 'assistant',
                content: content
            });
        }
    });
    
    if (messages.length > 0) {
        agentConversations[currentAgent] = messages;
    }
}

// Display agent conversation history
function displayAgentHistory(messages, agentName) {
    if (!messages || messages.length === 0) {
        showWelcome();
        return;
    }
    
    hideWelcome();
    
    messages.forEach(msg => {
        if (msg.role === 'user') {
            addMessageWithoutScroll(msg.content, 'user');
        } else {
            addMessageWithoutScroll(msg.content, 'assistant', agentName);
        }
    });
    
    scrollToBottom();
    
    // Save chat history after bulk loading
    saveCurrentChatSession();
}

// Add message without scrolling (for bulk adds)
function addMessageWithoutScroll(content, role, routedTo = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    let avatar;
    if (role === 'assistant') {
        avatar = '<i class="fas fa-robot"></i>';
    } else if (role === 'specialist') {
        avatar = '<i class="fas fa-headset"></i>';
    } else {
        avatar = '<i class="fas fa-user"></i>';
    }
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    let routedBadge = '';
    if (routedTo && (role === 'assistant' || role === 'specialist')) {
        const config = agentConfig[routedTo] || { name: routedTo };
        const icon = role === 'specialist' ? 'fa-headset' : 'fa-route';
        routedBadge = `<div class="routed-badge"><i class="fas ${icon}"></i> ${config.name}</div>`;
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            ${formatMessage(content)}
            ${routedBadge}
            <div class="message-meta">${time}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
}

// Update agent tabs UI without refetching
function updateAgentTabsUI() {
    const tabs = document.querySelectorAll('.agent-tab');
    tabs.forEach(tab => {
        const agent = tab.getAttribute('data-agent');
        if (agent === currentAgent) {
            tab.classList.add('active');
            // Remove new indicator when switched to
            const indicator = tab.querySelector('.new-indicator');
            if (indicator) indicator.remove();
        } else {
            tab.classList.remove('active');
        }
    });
}

// Clear messages from the container
function clearMessages() {
    messagesContainer.innerHTML = '';
}

// Auto-resize textarea
function autoResizeTextarea() {
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

// Handle keyboard
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Connect to escalation WebSocket for user
function connectEscalationWebSocket(escId) {
    escalationId = escId;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/user/${escalationId}`;
    
    console.log('*** USER CONNECTING TO WEBSOCKET ***:', wsUrl);
    addSystemMessage(`Connecting to live chat (${escId})...`);
    
    try {
        escalationWebSocket = new WebSocket(wsUrl);
        console.log('WebSocket object created');
    } catch (e) {
        console.error('Failed to create WebSocket:', e);
        addSystemMessage(`Error: Failed to create WebSocket connection: ${e.message}`);
        return;
    }
    
    escalationWebSocket.onopen = () => {
        console.log('*** USER WEBSOCKET CONNECTED ***');
        isEscalated = true;
        // Save escalation state for page refresh recovery
        saveEscalationState(escalationId);
        updateChatHeader('Connected to Specialist');
        updateEscalationBanner(true, escalationId);
        showLiveChatSection(escId);
        addSystemMessage('✓ Connected to live specialist chat! Your messages will be sent directly to the specialist.');
    };
    
    escalationWebSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('User received message from specialist:', data);
        
        if (data.type === 'specialist_message') {
            hideTypingIndicator();
            // Show specialist message prominently in the main chat
            addMessage(data.content, 'specialist', 'Human Specialist');
            // Save to local history backup
            appendToLocalHistory({ role: 'specialist', content: data.content, timestamp: data.timestamp });
            // Reset inactivity timer - specialist is active
            resetActivityTimer();
            // Play notification sound if available
            playNotificationSound();
        } else if (data.type === 'specialist_joined') {
            const specialistName = data.specialist_name || 'A specialist';
            addSystemMessage(`✓ ${specialistName} has joined the chat and can see your messages.`);
            updateChatHeader('Connected to Specialist');
            playNotificationSound();
        } else if (data.type === 'waiting_for_specialist') {
            addSystemMessage(`⏳ ${data.message || 'Waiting for a specialist to connect...'}`);
            updateChatHeader('Waiting for Specialist');
        } else if (data.type === 'servicenow_only') {
            addSystemMessage(`📋 ${data.message}`);
            if (data.servicenow_incident) {
                addSystemMessage(`Your ServiceNow ticket: ${data.servicenow_incident}`);
            }
            disconnectEscalation();
        } else if (data.type === 'specialist_disconnected') {
            addSystemMessage(`⚠️ ${data.message || 'The specialist has disconnected.'}`);
            playNotificationSound();
        } else if (data.type === 'specialist_typing') {
            showTypingIndicator();
        } else if (data.type === 'ticket_resolved') {
            // ServiceNow ticket was resolved by IT
            const resolvedBy = data.resolved_by || 'IT Support';
            const notes = data.resolution_notes || 'Your issue has been resolved.';
            addSystemMessage(`✅ Your ticket ${data.incident_number} has been resolved by ${resolvedBy}!`);
            addSystemMessage(`Resolution: ${notes}`);
            playNotificationSound();
        } else if (data.type === 'session_closed') {
            addSystemMessage('The chat session has ended. You can continue chatting with the AI assistant.');
            disconnectEscalation();
        } else if (data.type === 'user_connected') {
            // Confirmation that we're connected
            console.log('User connection confirmed');
        }
    };
    
    escalationWebSocket.onclose = (event) => {
        console.log('Escalation WebSocket closed:', event.code, event.reason);
        updateEscalationBanner(false, escalationId);
        
        // Handle specific close codes - don't reconnect for these
        if (event.code === 4003 || event.code === 4004) {
            // Session ended or not found - don't reconnect
            addSystemMessage(`Escalation session has ended: ${event.reason || 'Session closed'}`);
            disconnectEscalation();
            return;
        }
        
        if (event.code === 4002) {
            // ServiceNow-only ticket
            addSystemMessage('This request is being handled via ServiceNow ticketing system.');
            return;
        }
        
        // Attempt reconnect for other disconnects
        if (isEscalated && escalationId) {
            addSystemMessage('Connection to specialist lost. Attempting to reconnect...');
            setTimeout(() => {
                if (escalationId) connectEscalationWebSocket(escalationId);
            }, 3000);
        }
    };
    
    escalationWebSocket.onerror = (error) => {
        console.error('*** WEBSOCKET ERROR ***:', error);
        updateEscalationBanner(false, escalationId);
        addSystemMessage('Connection error. Click "Reconnect" in the banner to try again.');
    };
}

// Play notification sound
function playNotificationSound() {
    try {
        const audio = new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU');
        audio.volume = 0.3;
        audio.play().catch(() => {});
    } catch (e) {}
}

// Show live chat section in sidebar
function showLiveChatSection(escId) {
    const section = document.getElementById('liveChatSection');
    const info = document.getElementById('liveChatInfo');
    if (section && info) {
        section.style.display = 'block';
        info.innerHTML = `
            <p><strong>Session:</strong> ${escId}</p>
            <p><strong>Status:</strong> <span class="connected-status">Connected</span></p>
            <p class="hint">Your messages now go directly to the specialist</p>
        `;
    }
}

// Hide live chat section
function hideLiveChatSection() {
    const section = document.getElementById('liveChatSection');
    if (section) {
        section.style.display = 'none';
    }
}

// Update escalation banner state
function updateEscalationBanner(connected, escId) {
    const banner = document.getElementById('escalationBanner');
    if (banner) {
        if (connected) {
            banner.className = 'escalation-banner connected';
            banner.querySelector('.banner-content').innerHTML = `
                <i class="fas fa-check-circle"></i>
                <span>Live Chat Active (${escId}) - Your messages go directly to the specialist</span>
                <button onclick="disconnectEscalation()" class="banner-btn">
                    <i class="fas fa-times"></i> End Chat
                </button>
            `;
        } else {
            banner.className = 'escalation-banner';
            banner.querySelector('.banner-content').innerHTML = `
                <i class="fas fa-exclamation-circle"></i>
                <span>Disconnected from specialist (${escId})</span>
                <button onclick="manualConnectEscalation('${escId}')" class="banner-btn">
                    <i class="fas fa-sync"></i> Reconnect
                </button>
            `;
        }
    }
}

// Disconnect from escalation (user manually ends chat)
function disconnectEscalation() {
    // Cancel any inactivity timer
    cancelInactivityTimer();
    pendingNewChat = false;
    
    isEscalated = false;
    const currentEscId = escalationId;
    
    // Close WebSocket but DON'T clear state yet - keep for history
    if (escalationWebSocket) {
        escalationWebSocket.close();
        escalationWebSocket = null;
    }
    
    updateChatHeader('CorpAssist');
    
    // Update banner to show reconnect option instead of removing it
    const banner = document.getElementById('escalationBanner');
    if (banner && currentEscId) {
        banner.className = 'escalation-banner ended';
        banner.querySelector('.banner-content').innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span>Live chat session ended (${currentEscId})</span>
            <button onclick="attemptReconnect('${currentEscId}')" class="banner-btn">
                <i class="fas fa-sync"></i> Reconnect
            </button>
            <button onclick="closeEscalationBanner()" class="banner-btn secondary">
                <i class="fas fa-times"></i> Dismiss
            </button>
        `;
    }
    
    // Hide sidebar live chat section
    hideLiveChatSection();
    
    escalationId = null;
    addSystemMessage('Live chat ended. You can reconnect if the session is still active, or continue chatting with the AI assistant to request a new specialist.');
}

// Close escalation banner and clear state (final dismissal)
function closeEscalationBanner() {
    const banner = document.getElementById('escalationBanner');
    if (banner) {
        banner.remove();
    }
    clearEscalationState();
}

// Attempt to reconnect to an escalation session
async function attemptReconnect(escId) {
    try {
        addSystemMessage('Checking if session is still active...');
        
        const response = await fetch(`/api/escalation/${escId}/status`);
        
        if (!response.ok) {
            if (response.status === 404) {
                addSystemMessage('Session not found. Please ask the AI assistant to connect you with a specialist.');
                closeEscalationBanner();
                return;
            }
            throw new Error('Failed to check session status');
        }
        
        const data = await response.json();
        
        if (data.status === 'closed' || data.status === 'resolved') {
            addSystemMessage(`This session has ended (${data.status}). Please ask the AI assistant to connect you with a specialist for a new session.`);
            closeEscalationBanner();
            return;
        }
        
        // Session still active - reconnect!
        addSystemMessage('Session is still active. Reconnecting...');
        escalationId = escId;
        isEscalated = true;
        saveEscalationState(escId);
        connectEscalationWebSocket(escId);
        
    } catch (error) {
        console.error('Reconnect failed:', error);
        addSystemMessage('Failed to reconnect. Please try again or ask for a new specialist.');
    }
}
}

// Update chat header to show specialist mode
function updateChatHeader(text) {
    const statusEl = document.querySelector('.chat-header .status');
    if (statusEl) {
        if (isEscalated) {
            statusEl.innerHTML = `<span class="status-dot live"></span> ${text}`;
            statusEl.classList.add('specialist-mode');
        } else {
            statusEl.innerHTML = `<span class="status-dot"></span> Available 24/7`;
            statusEl.classList.remove('specialist-mode');
        }
    }
}

// Add system message
function addSystemMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message system-message';
    msgDiv.innerHTML = `
        <div class="system-content">
            <i class="fas fa-info-circle"></i> ${text}
        </div>
    `;
    messagesContainer.appendChild(msgDiv);
    scrollToBottom();
    
    // Save chat history after system message
    saveCurrentChatSession();
}

// Start a new chat session (clears history)
function startNewChat() {
    // Check if there's an active live chat with specialist
    if (isEscalated && escalationWebSocket && escalationWebSocket.readyState === WebSocket.OPEN) {
        // Don't close immediately - warn user and start inactivity timer
        if (!pendingNewChat) {
            pendingNewChat = true;
            addSystemMessage('⚠️ You have an active live chat with a specialist. The chat will automatically end after 2 minutes of inactivity, or you can click "New Conversation" again to end it now.');
            startInactivityTimer();
            return;
        } else {
            // User clicked again - they really want to end it
            addSystemMessage('Ending live chat session...');
            disconnectEscalation();
            pendingNewChat = false;
        }
    }
    
    // Cancel any pending inactivity timer
    cancelInactivityTimer();
    pendingNewChat = false;
    
    // Save current chat session before starting new one
    saveCurrentChatSession();
    
    // Clear escalation state
    clearEscalationState();
    
    // Clear the message display
    messagesContainer.innerHTML = '';
    
    // Reset state
    agentConversations = {};
    currentAgent = null;
    lastRoutedAgent = null;
    
    // Create new session ID
    currentChatSessionId = generateChatSessionId();
    localStorage.setItem(CURRENT_SESSION_KEY, currentChatSessionId);
    
    // Hide agent tabs
    const tabsContainer = document.getElementById('agentTabsContainer');
    if (tabsContainer) {
        tabsContainer.style.display = 'none';
    }
    
    // Show welcome message
    showWelcome();
    
    console.log('Started new chat session:', currentChatSessionId);
}

// Track activity (called when messages are sent/received)
function resetActivityTimer() {
    lastActivityTime = Date.now();
    
    // If we have a pending new chat with inactivity timer, restart it
    if (pendingNewChat && inactivityTimer) {
        startInactivityTimer();
    }
}

// Start inactivity timer for auto-closing live chat
function startInactivityTimer() {
    cancelInactivityTimer();
    lastActivityTime = Date.now();
    
    inactivityTimer = setTimeout(() => {
        checkInactivity();
    }, INACTIVITY_TIMEOUT);
    
    console.log('Inactivity timer started - will check in 2 minutes');
}

// Cancel inactivity timer
function cancelInactivityTimer() {
    if (inactivityTimer) {
        clearTimeout(inactivityTimer);
        inactivityTimer = null;
    }
}

// Check if chat has been inactive and should auto-close
function checkInactivity() {
    const now = Date.now();
    const timeSinceLastActivity = now - (lastActivityTime || 0);
    
    if (timeSinceLastActivity >= INACTIVITY_TIMEOUT) {
        // 2 minutes of inactivity - auto close
        addSystemMessage('💤 Live chat ended due to 2 minutes of inactivity.');
        disconnectEscalation();
        pendingNewChat = false;
        cancelInactivityTimer();
        
        // Now proceed with new chat
        setTimeout(() => {
            // Save current session before creating new one
            saveCurrentChatSession();
            clearEscalationState();
            messagesContainer.innerHTML = '';
            agentConversations = {};
            currentAgent = null;
            lastRoutedAgent = null;
            currentChatSessionId = generateChatSessionId();
            localStorage.setItem(CURRENT_SESSION_KEY, currentChatSessionId);
            showWelcome();
            console.log('New chat started after inactivity timeout');
        }, 1500);
    } else {
        // Still active, restart timer for remaining time
        const remainingTime = INACTIVITY_TIMEOUT - timeSinceLastActivity;
        inactivityTimer = setTimeout(() => {
            checkInactivity();
        }, remainingTime);
    }
}

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isLoading) return;
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // Hide welcome message
    hideWelcome();
    
    // Add user message
    addMessage(message, 'user');
    
    // If escalated, send via WebSocket to specialist
    if (isEscalated && escalationWebSocket && escalationWebSocket.readyState === WebSocket.OPEN) {
        const timestamp = new Date().toISOString();
        escalationWebSocket.send(JSON.stringify({
            type: 'user_message',
            content: message,
            timestamp: timestamp
        }));
        // Save to local history backup
        appendToLocalHistory({ role: 'user', content: message, timestamp: timestamp });
        // Reset inactivity timer - user is active
        resetActivityTimer();
        return;
    }
    
    // Show loading
    setLoading(true);
    showTypingIndicator();
    
    try {
        const timeInfo = getCurrentTimeInfo();
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message, 
                session_id: sessionId,
                user_timezone: userTimezone,
                user_local_time: timeInfo.localTime,
                user_local_date: timeInfo.localDate
            })
        });
        
        const data = await response.json();
        
        // Update session ID if new
        if (data.session_id) {
            sessionId = data.session_id;
        }
        
        // Track which agent responded
        if (data.routed_to) {
            lastRoutedAgent = data.routed_to;
            // If we were viewing a different agent's history, update current agent
            if (currentAgent === null || data.routed_to !== currentAgent) {
                // Agent switched - update tracking
                currentAgent = data.routed_to;
            }
        }
        
        // Remove typing indicator and add response
        hideTypingIndicator();
        addMessage(data.response, 'assistant', data.routed_to);
        
        // Update agent tabs after each message
        fetchAgentConversations();
        
        // Check if response contains an escalation
        checkForEscalation(data.response);
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addMessage('Sorry, there was an error processing your request. Please try again.', 'assistant');
    } finally {
        setLoading(false);
    }
}

// Check if response contains an escalation link and connect
function checkForEscalation(response) {
    console.log('Checking for escalation in response:', response.substring(0, 300));
    
    // Look for escalation ID pattern in response (ESC- followed by 14 digits)
    const escMatch = response.match(/ESC-\d{14}/);
    if (escMatch) {
        const escId = escMatch[0];
        console.log('*** ESCALATION DETECTED ***:', escId);
        alert(`Escalation detected: ${escId}\nConnecting to live chat...`);
        
        // Show connection banner
        showEscalationBanner(escId);
        
        // Connect to escalation WebSocket immediately
        connectEscalationWebSocket(escId);
    } else {
        console.log('No escalation pattern found');
    }
}

// Show escalation banner for user to connect
function showEscalationBanner(escId) {
    // Remove any existing banner
    const existingBanner = document.getElementById('escalationBanner');
    if (existingBanner) existingBanner.remove();
    
    const banner = document.createElement('div');
    banner.id = 'escalationBanner';
    banner.className = 'escalation-banner';
    banner.innerHTML = `
        <div class="banner-content">
            <i class="fas fa-headset"></i>
            <span>Connecting to live specialist (${escId})...</span>
            <button onclick="manualConnectEscalation('${escId}')" class="banner-btn">
                <i class="fas fa-sync"></i> Reconnect
            </button>
        </div>
    `;
    
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.insertBefore(banner, chatContainer.querySelector('.messages-container'));
    }
}

// Manual reconnect function
function manualConnectEscalation(escId) {
    console.log('Manual reconnect to:', escId);
    addSystemMessage(`Reconnecting to escalation ${escId}...`);
    connectEscalationWebSocket(escId);
}

// Send quick message (from sidebar)
function sendQuickMessage(message) {
    messageInput.value = message;
    sendMessage();
}

// Add message to chat
function addMessage(content, role, routedTo = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    let avatar;
    if (role === 'assistant') {
        avatar = '<i class="fas fa-robot"></i>';
    } else if (role === 'specialist') {
        avatar = '<i class="fas fa-headset"></i>';
    } else {
        avatar = '<i class="fas fa-user"></i>';
    }
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    let routedBadge = '';
    if (routedTo && (role === 'assistant' || role === 'specialist')) {
        const agentNames = {
            'hr_agent': 'HR Support',
            'it_support_agent': 'IT Support',
            'sales_agent': 'Sales Support',
            'legal_agent': 'Legal Support',
            'off_topic_agent': 'General',
            'Human Specialist': 'Human Specialist'
        };
        const displayName = agentNames[routedTo] || routedTo;
        const icon = role === 'specialist' ? 'fa-headset' : 'fa-route';
        routedBadge = `<div class="routed-badge"><i class="fas ${icon}"></i> ${displayName}</div>`;
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            ${formatMessage(content)}
            ${routedBadge}
            <div class="message-meta">${time}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    
    // Save chat history after each message
    saveCurrentChatSession();
}

// Format message content
function formatMessage(content) {
    // Convert URLs to links
    content = content.replace(
        /(https?:\/\/[^\s]+)/g,
        '<a href="$1" target="_blank" rel="noopener">$1</a>'
    );
    
    // Convert newlines to breaks
    content = content.replace(/\n/g, '<br>');
    
    // Bold text between ** **
    content = content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Code blocks
    content = content.replace(/`(.+?)`/g, '<code>$1</code>');
    
    return content;
}

// Show typing indicator
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="message-avatar"><i class="fas fa-robot"></i></div>
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

// Hide welcome message
function hideWelcome() {
    const welcome = document.querySelector('.welcome-message');
    if (welcome) {
        welcome.style.display = 'none';
    }
}

// Show welcome message
function showWelcome() {
    const welcome = document.querySelector('.welcome-message');
    if (welcome) {
        welcome.style.display = 'block';
    }
}

// Set loading state
function setLoading(loading) {
    isLoading = loading;
    sendBtn.disabled = loading;
}

// Scroll to bottom
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Toggle theme
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    body.setAttribute('data-theme', newTheme);
    
    // Update icon
    const icon = document.querySelector('.header-actions .icon-btn i');
    icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    
    // Save preference
    localStorage.setItem('theme', newTheme);
}

// Load saved theme
(function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
})();
