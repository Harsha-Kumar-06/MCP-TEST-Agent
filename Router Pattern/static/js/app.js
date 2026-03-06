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
    console.log('Escalation state cleared');
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
                addSystemMessage(`Previous chat session (${reason}). Click "New Chat" to start fresh.`);
                showChatEndedState();
            } else {
                // Active session - reconnect
                console.log('Restoring active escalation:', storedEscalationId);
                addSystemMessage(`Reconnecting to live chat session...`);
                connectEscalationWebSocket(storedEscalationId);
            }
            
        } else if (response.status === 404) {
            // Escalation not found on server - show local history if available
            console.log('Escalation not found on server');
            addSystemMessage(`Previous session not found. Click "New Chat" to start fresh.`);
            showChatEndedState();
        }
    } catch (error) {
        console.error('Failed to check escalation status:', error);
        // Network error - try to load history and reconnect
        await loadEscalationHistory(storedEscalationId);
        addSystemMessage(`Attempting to reconnect...`);
        connectEscalationWebSocket(storedEscalationId);
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
            
            // Hide welcome message
            hideWelcome();
            
            // Display chat history
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    if (msg.role === 'user') {
                        addMessageWithoutScroll(msg.content, 'user');
                    } else if (msg.role === 'specialist') {
                        addMessageWithoutScroll(msg.content, 'specialist', 'Human Specialist');
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
        }
    } catch (error) {
        console.error('Failed to load escalation history:', error);
    }
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

// Disconnect from escalation
function disconnectEscalation() {
    isEscalated = false;
    const currentEscId = escalationId;
    escalationId = null;
    
    // Clear saved escalation state
    clearEscalationState();
    
    if (escalationWebSocket) {
        escalationWebSocket.close();
        escalationWebSocket = null;
    }
    updateChatHeader('CorpAssist');
    
    // Remove banner
    const banner = document.getElementById('escalationBanner');
    if (banner) {
        banner.remove();
    }
    
    // Hide sidebar live chat section
    hideLiveChatSection();
    
    addSystemMessage('Live chat ended. You can continue chatting with the AI assistant.');
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
        escalationWebSocket.send(JSON.stringify({
            type: 'user_message',
            content: message,
            timestamp: new Date().toISOString()
        }));
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

// Start new chat
async function startNewChat() {
    // Disconnect any active escalation
    if (isEscalated || escalationId) {
        disconnectEscalation();
    }
    
    // Clear escalation state from localStorage
    clearEscalationState();
    
    // Remove chat ended banner if present
    const chatEndedBanner = document.getElementById('chatEndedBanner');
    if (chatEndedBanner) {
        chatEndedBanner.remove();
    }
    
    // Clear messages
    messagesContainer.innerHTML = '';
    
    // Reset agent conversation state
    agentConversations = {};
    currentAgent = null;
    lastRoutedAgent = null;
    
    // Clear stored session to get a fresh one
    localStorage.removeItem('corpassist_session_id');
    
    // Hide agent tabs
    const tabsContainer = document.getElementById('agentTabsContainer');
    if (tabsContainer) {
        tabsContainer.style.display = 'none';
    }
    
    // Get new session
    try {
        const response = await fetch('/api/session/new', { method: 'POST' });
        const data = await response.json();
        sessionId = data.session_id;
        localStorage.setItem('corpassist_session_id', sessionId);
        console.log('New session created:', sessionId);
    } catch (error) {
        console.error('Failed to create new session:', error);
    }
    
    // Show welcome
    const welcomeHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">
                <img src="/static/images/logo.svg" alt="CorpAssist" class="welcome-logo">
            </div>
            <h2>Welcome to CorpAssist</h2>
            <p>I'm your AI-powered workplace assistant. I can help you with:</p>
            <div class="capabilities">
                <div class="capability">
                    <i class="fas fa-laptop-code"></i>
                    <span><strong>IT Support</strong><br>Hardware, software, access issues</span>
                </div>
                <div class="capability">
                    <i class="fas fa-user-tie"></i>
                    <span><strong>HR</strong><br>PTO, benefits, policies</span>
                </div>
                <div class="capability">
                    <i class="fas fa-handshake"></i>
                    <span><strong>Sales</strong><br>Quotes, CRM, customers</span>
                </div>
                <div class="capability">
                    <i class="fas fa-balance-scale"></i>
                    <span><strong>Legal</strong><br>Contracts, compliance, NDAs</span>
                </div>
            </div>
            <p class="hint">Try: "My laptop is slow and I need a license for Adobe"</p>
        </div>
    `;
    messagesContainer.innerHTML = welcomeHTML;
    
    // Get new session
    await initSession();
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
