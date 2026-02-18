/**
 * CorpAssist - Specialist Console JavaScript
 * Enables real-time chat between specialists and users
 */

// State
let escalationId = null;
let specialistToken = null;
let sessionId = null;
let websocket = null;
let isConnected = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// DOM Elements
const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const connectionStatus = document.getElementById('connectionStatus');
const escalationInfo = document.getElementById('escalationInfo');
const userInfoPanel = document.getElementById('userInfoPanel');
const userDetails = document.getElementById('userDetails');
const chatStatus = document.getElementById('chatStatus');
const specialistWelcome = document.getElementById('specialistWelcome');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    parseUrlParams();
    if (escalationId && specialistToken) {
        validateAndConnect();
    } else {
        showInvalidSession();
    }
});

// Parse URL parameters
function parseUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    escalationId = urlParams.get('escalation_id') || urlParams.get('id');
    specialistToken = urlParams.get('token');
    
    console.log('Escalation ID:', escalationId);
    console.log('Token present:', !!specialistToken);
}

// Validate session and connect
async function validateAndConnect() {
    try {
        updateConnectionStatus('connecting', 'Validating session...');
        
        const response = await fetch(`/api/specialist/validate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                escalation_id: escalationId,
                token: specialistToken
            })
        });
        
        if (!response.ok) {
            throw new Error('Invalid session');
        }
        
        const data = await response.json();
        sessionId = data.session_id;
        
        // Display escalation info
        displayEscalationInfo(data);
        
        // Connect WebSocket
        connectWebSocket();
        
        // Load chat history
        loadChatHistory();
        
    } catch (error) {
        console.error('Validation failed:', error);
        showInvalidSession();
    }
}

// Connect to WebSocket for real-time messaging
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/specialist/${escalationId}?token=${specialistToken}`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    
    websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
        console.log('WebSocket connected');
        isConnected = true;
        reconnectAttempts = 0;
        updateConnectionStatus('connected', 'Connected');
        enableInput();
        hideWelcome();
        
        // Notify that specialist has joined
        websocket.send(JSON.stringify({
            type: 'specialist_joined',
            escalation_id: escalationId
        }));
    };
    
    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    websocket.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        isConnected = false;
        updateConnectionStatus('disconnected', 'Disconnected');
        disableInput();
        
        // Attempt to reconnect
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            updateConnectionStatus('connecting', `Reconnecting (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
            setTimeout(connectWebSocket, 2000 * reconnectAttempts);
        }
    };
    
    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus('error', 'Connection error');
    };
}

// Handle incoming WebSocket messages
function handleWebSocketMessage(data) {
    console.log('Received message:', data);
    
    switch (data.type) {
        case 'user_message':
            addMessage(data.content, 'user', data.timestamp);
            playNotificationSound();
            break;
            
        case 'ai_message':
            addMessage(data.content, 'ai', data.timestamp);
            break;
            
        case 'specialist_message':
            // Our own message confirmed
            break;
            
        case 'chat_history':
            displayChatHistory(data.messages);
            break;
            
        case 'user_typing':
            showUserTyping();
            break;
            
        case 'user_connected':
            updateChatStatus('User is online');
            break;
            
        case 'user_disconnected':
            updateChatStatus('User went offline');
            break;
            
        case 'session_closed':
            showSessionClosed();
            break;
            
        case 'error':
            showError(data.message);
            break;
    }
}

// Display escalation information
function displayEscalationInfo(data) {
    escalationInfo.innerHTML = `
        <h3><i class="fas fa-ticket-alt"></i> Escalation Details</h3>
        <div class="info-item">
            <label>Escalation ID</label>
            <span>${data.escalation_id}</span>
        </div>
        <div class="info-item">
            <label>Department</label>
            <span>${data.department || 'N/A'}</span>
        </div>
        <div class="info-item">
            <label>Urgency</label>
            <span class="urgency-badge ${data.urgency || 'normal'}">${(data.urgency || 'normal').toUpperCase()}</span>
        </div>
        <div class="info-item">
            <label>Created</label>
            <span>${formatDateTime(data.created_at)}</span>
        </div>
        ${data.servicenow_incident ? `
        <div class="info-item">
            <label>ServiceNow</label>
            <span><a href="${data.servicenow_url || '#'}" target="_blank">${data.servicenow_incident}</a></span>
        </div>
        ` : ''}
        <div class="info-item issue-summary">
            <label>Issue Summary</label>
            <p>${data.issue_summary || 'No summary available'}</p>
        </div>
    `;
    
    // Display user info if available
    if (data.user) {
        userInfoPanel.style.display = 'block';
        userDetails.innerHTML = `
            <div class="info-item">
                <label>Name</label>
                <span>${data.user.full_name || data.user.employee_id}</span>
            </div>
            <div class="info-item">
                <label>Email</label>
                <span>${data.user.email || 'N/A'}</span>
            </div>
            <div class="info-item">
                <label>Department</label>
                <span>${data.user.department || 'N/A'}</span>
            </div>
        `;
    }
}

// Load chat history
async function loadChatHistory() {
    try {
        const response = await fetch(`/api/specialist/history/${escalationId}?token=${specialistToken}`);
        if (response.ok) {
            const data = await response.json();
            displayChatHistory(data.messages);
        }
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

// Display chat history
function displayChatHistory(messages) {
    if (!messages || messages.length === 0) {
        addSystemMessage('Chat session started. Waiting for user messages...');
        return;
    }
    
    messages.forEach(msg => {
        addMessage(msg.content, msg.role, msg.timestamp);
    });
    
    scrollToBottom();
}

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || !isConnected) return;
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // Add message to UI immediately
    addMessage(message, 'specialist');
    
    // Send via WebSocket
    websocket.send(JSON.stringify({
        type: 'specialist_message',
        content: message,
        escalation_id: escalationId
    }));
}

// Send quick response
function sendQuickResponse(message) {
    messageInput.value = message;
    sendMessage();
}

// Add message to chat
function addMessage(content, role, timestamp = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    let avatar, label;
    switch (role) {
        case 'user':
            avatar = '<i class="fas fa-user"></i>';
            label = 'User';
            break;
        case 'specialist':
            avatar = '<i class="fas fa-headset"></i>';
            label = 'You (Specialist)';
            break;
        case 'ai':
            avatar = '<i class="fas fa-robot"></i>';
            label = 'AI Assistant';
            break;
        default:
            avatar = '<i class="fas fa-info-circle"></i>';
            label = 'System';
    }
    
    const time = timestamp ? formatTime(timestamp) : formatTime(new Date().toISOString());
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">${label}</span>
            </div>
            ${formatMessage(content)}
            <div class="message-meta">${time}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Add system message
function addSystemMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'system-message';
    messageDiv.innerHTML = `<i class="fas fa-info-circle"></i> ${content}`;
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
    
    return content;
}

// Format time
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Format date time
function formatDateTime(timestamp) {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// Update connection status
function updateConnectionStatus(status, text) {
    connectionStatus.className = `connection-status ${status}`;
    connectionStatus.innerHTML = `<i class="fas fa-circle"></i> <span>${text}</span>`;
}

// Update chat status
function updateChatStatus(text) {
    chatStatus.innerHTML = `<span class="status-dot"></span> ${text}`;
}

// Show user typing indicator
function showUserTyping() {
    updateChatStatus('User is typing...');
    setTimeout(() => {
        updateChatStatus('Connected to user');
    }, 3000);
}

// Enable input
function enableInput() {
    messageInput.disabled = false;
    sendBtn.disabled = false;
    messageInput.placeholder = 'Type your response to the user...';
}

// Disable input
function disableInput() {
    messageInput.disabled = true;
    sendBtn.disabled = true;
    messageInput.placeholder = 'Disconnected - Reconnecting...';
}

// Hide welcome screen
function hideWelcome() {
    if (specialistWelcome) {
        specialistWelcome.style.display = 'none';
    }
}

// Scroll to bottom
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Handle keyboard
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Play notification sound (optional)
function playNotificationSound() {
    // Can implement audio notification here
    // const audio = new Audio('/static/sounds/notification.mp3');
    // audio.play().catch(() => {});
}

// Show invalid session modal
function showInvalidSession() {
    document.getElementById('invalidSessionModal').style.display = 'flex';
}

// Show session closed modal
function showSessionClosed() {
    disableInput();
    document.getElementById('sessionClosedModal').style.display = 'flex';
}

// Show error
function showError(message) {
    addSystemMessage(`Error: ${message}`);
}

// Show resolution modal
function closeSession() {
    const modal = document.getElementById('resolutionModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

// Hide resolution modal
function hideResolutionModal() {
    const modal = document.getElementById('resolutionModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Confirm close session with resolution notes
async function confirmCloseSession() {
    const resolutionNotes = document.getElementById('resolutionNotes')?.value || '';
    const resolutionCode = document.getElementById('resolutionCode')?.value || 'Solved (Permanently)';
    
    if (!resolutionNotes.trim()) {
        alert('Please enter resolution notes before closing.');
        return;
    }
    
    hideResolutionModal();
    
    try {
        await fetch(`/api/specialist/close/${escalationId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                token: specialistToken,
                resolution_notes: resolutionNotes,
                resolution_code: resolutionCode
            })
        });
        
        if (websocket) {
            websocket.send(JSON.stringify({
                type: 'session_closed',
                escalation_id: escalationId
            }));
            websocket.close();
        }
        
        showSessionClosed();
    } catch (error) {
        console.error('Failed to close session:', error);
    }
}

// Toggle theme
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const icon = document.querySelector('.header-actions .icon-btn i');
    if (document.body.classList.contains('dark-theme')) {
        icon.className = 'fas fa-sun';
    } else {
        icon.className = 'fas fa-moon';
    }
}

// Auto-resize textarea
messageInput?.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});
