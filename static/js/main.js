// MITChat JavaScript (2025-01-08T12:20:30-05:00)

let currentUsername = 'anonymous';
let messageVerificationEnabled = false;

// Available reactions
const REACTIONS = ['👍', '❤️', '😄', '🤔'];

// Scroll handling
let isInitialLoad = true;
let lastScrollHeight = 0;
let lastScrollTop = 0;

function isAtBottom() {
    const messages = document.getElementById('messages');
    const threshold = 100; // pixels from bottom to consider "at bottom"
    return messages.scrollHeight - messages.scrollTop - messages.clientHeight <= threshold;
}

function scrollToBottom(force = false) {
    const messages = document.getElementById('messages');
    const anchor = document.getElementById('scroll-anchor');
    
    if (force || isInitialLoad || isAtBottom()) {
        // Use IntersectionObserver to ensure the scroll happens after content is fully rendered
        const observer = new IntersectionObserver((entries) => {
            entries[0].target.scrollIntoView({ behavior: 'instant' });
            observer.disconnect();
        });
        observer.observe(anchor);
    }
}

// Initialize everything
document.addEventListener('DOMContentLoaded', async () => {
    await verifyUsername();
    setupMessageInput();
    setupUsernameUI();
    await loadMessages();
    
    // Set up scroll position maintenance
    const messages = document.getElementById('messages');
    messages.addEventListener('scroll', () => {
        lastScrollTop = messages.scrollTop;
        lastScrollHeight = messages.scrollHeight;
    });
});

// Helper function to verify username
async function verifyUsername() {
    try {
        const response = await fetch('/verify_username');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        currentUsername = data.username;
        
        // Update localStorage with the verified username
        localStorage.setItem('username', currentUsername);
        
        // Update UI if it exists
        const usernameDisplay = document.getElementById('current-username');
        if (usernameDisplay) {
            usernameDisplay.textContent = `Current username: ${currentUsername}`;
        }
        
        return data.status === 'verified';
    } catch (error) {
        console.error('Error verifying username:', error);
        // Fall back to stored username or anonymous
        currentUsername = localStorage.getItem('username') || 'anonymous';
        return false;
    }
}

async function loadMessages() {
    try {
        const response = await fetch('/messages');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        let messages = data.messages;
        messageVerificationEnabled = data.messageVerificationEnabled;
        
        if (messageVerificationEnabled) {
            messages = messages.filter(message => message.verified && message.verified.toLowerCase() === 'true');
        }
        
        const messagesDiv = document.getElementById('messages');
        const messagesContainer = document.getElementById('messages-container');
        
        // Remember scroll position before updating content
        lastScrollHeight = messagesDiv.scrollHeight;
        lastScrollTop = messagesDiv.scrollTop;
        
        // Clear and rebuild messages
        messagesContainer.innerHTML = '';
        messages.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
        
        for (const message of messages) {
            messagesContainer.appendChild(createMessageElement(message));
        }
        
        // Handle scroll position
        if (isInitialLoad) {
            scrollToBottom(true);
            isInitialLoad = false;
        } else {
            scrollToBottom();
        }
        
        // Update current username
        if (data.currentUsername) {
            currentUsername = data.currentUsername;
            localStorage.setItem('username', currentUsername);
            const usernameDisplay = document.getElementById('current-username');
            if (usernameDisplay) {
                usernameDisplay.textContent = `Current username: ${currentUsername}`;
            }
        }
        
        // Update verification status
        updateGlobalVerificationStatus();
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

function formatMessageDate(date) {
    const now = new Date('2025-01-14T15:04:15-05:00');  // Current time
    const messageDate = new Date(date);
    const diffDays = Math.floor((now - messageDate) / (1000 * 60 * 60 * 24));
    
    // Format time
    const timeStr = messageDate.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
    }).toLowerCase();
    
    // Format date based on how old it is
    if (diffDays < 7) {
        // Within last week - show day of week
        const dayOfWeek = messageDate.toLocaleDateString('en-US', { weekday: 'long' });
        if (diffDays === 0) {
            return `${timeStr} today`;
        } else if (diffDays === 1) {
            return `${timeStr} yesterday`;
        } else {
            return `${timeStr} on ${dayOfWeek}`;
        }
    } else {
        // Older than a week - show full date
        const dateStr = messageDate.toLocaleDateString('en-US', { 
            month: 'short',
            day: 'numeric',
            year: messageDate.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        });
        return `${timeStr} on ${dateStr}`;
    }
}

function createMessageElement(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    messageDiv.className += message.author === currentUsername ? ' right' : ' left';
    messageDiv.dataset.messageId = message.id;
    
    // Add author name above bubble
    const authorDiv = document.createElement('div');
    authorDiv.className = 'message-author';
    authorDiv.textContent = message.author || 'anonymous';
    messageDiv.appendChild(authorDiv);
    
    // Create content wrapper for positioning
    const contentWrapper = document.createElement('div');
    contentWrapper.className = 'message-content-wrapper';
    
    // Create message content
    const content = document.createElement('div');
    content.className = 'message-content';
    let messageText = message.content;
    messageText = messageText.replace(/^(Date|Author|Message):[^\n]*\n/gm, '');
    messageText = messageText.trim();
    content.textContent = messageText;
    
    // Add reaction button inside content wrapper
    const reactionButton = document.createElement('button');
    reactionButton.className = 'reaction-button';
    reactionButton.textContent = '😀';
    reactionButton.title = 'Add reaction';
    reactionButton.onclick = (e) => {
        e.stopPropagation();
        toggleReactionPicker(contentWrapper);
    };
    
    // Create reaction picker (hidden by default)
    const reactionPicker = document.createElement('div');
    reactionPicker.className = 'reaction-picker';
    REACTIONS.forEach(emoji => {
        const emojiButton = document.createElement('span');
        emojiButton.className = 'reaction-picker-emoji';
        emojiButton.textContent = emoji;
        emojiButton.onclick = (e) => {
            e.stopPropagation();
            toggleReaction(message.id, emoji);
            reactionPicker.classList.remove('active');
        };
        reactionPicker.appendChild(emojiButton);
    });
    
    contentWrapper.appendChild(content);
    contentWrapper.appendChild(reactionButton);
    contentWrapper.appendChild(reactionPicker);
    
    // Create reactions container
    const reactionsContainer = document.createElement('div');
    reactionsContainer.className = 'reactions-container';
    
    // Add existing reactions
    if (message.reactions) {
        Object.entries(message.reactions).forEach(([emoji, users]) => {
            if (users.length > 0) {
                const reaction = document.createElement('div');
                reaction.className = 'reaction';
                if (users.includes(currentUsername)) {
                    reaction.className += ' active';
                }
                reaction.onclick = () => toggleReaction(message.id, emoji);
                reaction.innerHTML = `${emoji} <span>${users.length}</span>`;
                reactionsContainer.appendChild(reaction);
            }
        });
    }
    
    contentWrapper.appendChild(reactionsContainer);
    messageDiv.appendChild(contentWrapper);
    
    // Create message metadata
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    
    // Add timestamp
    const timestampSpan = document.createElement('span');
    timestampSpan.className = 'message-time';
    if (message.pending) {
        timestampSpan.textContent = 'Sending...';
    } else {
        timestampSpan.textContent = formatMessageDate(message.createdAt);
    }
    meta.appendChild(timestampSpan);
    
    messageDiv.appendChild(meta);
    return messageDiv;
}

// Toggle reaction picker visibility
function toggleReactionPicker(contentWrapper) {
    const picker = contentWrapper.querySelector('.reaction-picker');
    const allPickers = document.querySelectorAll('.reaction-picker.active');
    allPickers.forEach(p => {
        if (p !== picker) p.classList.remove('active');
    });
    picker.classList.toggle('active');
}

// Toggle a reaction on a message
async function toggleReaction(messageId, emoji) {
    try {
        const response = await fetch(`/messages/${messageId}/reactions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ emoji })
        });
        
        if (!response.ok) {
            throw new Error('Failed to toggle reaction');
        }
        
        // Get the updated message with reactions
        const updatedMessage = await response.json();
        
        // Find and update the message element
        const messageDiv = document.querySelector(`.message[data-message-id="${messageId}"]`);
        if (messageDiv) {
            // Update reactions container
            const reactionsContainer = messageDiv.querySelector('.reactions-container');
            reactionsContainer.innerHTML = ''; // Clear existing reactions
            
            // Add updated reactions
            if (updatedMessage.reactions) {
                Object.entries(updatedMessage.reactions).forEach(([emoji, users]) => {
                    if (users.length > 0) {
                        const reaction = document.createElement('div');
                        reaction.className = 'reaction';
                        if (users.includes(currentUsername)) {
                            reaction.className += ' active';
                        }
                        reaction.onclick = () => toggleReaction(messageId, emoji);
                        reaction.innerHTML = `${emoji} <span>${users.length}</span>`;
                        reactionsContainer.appendChild(reaction);
                    }
                });
            }
        }
    } catch (error) {
        console.error('Error toggling reaction:', error);
    }
}

// Close reaction pickers when clicking outside
document.addEventListener('click', () => {
    const activePickers = document.querySelectorAll('.reaction-picker.active');
    activePickers.forEach(picker => picker.classList.remove('active'));
});

async function sendMessage(content, type = 'message') {
    try {
        // Create a temporary message object
        const tempMessage = {
            content: content,
            author: currentUsername,
            createdAt: new Date().toISOString(),
            id: 'pending-' + Date.now(),
            verified: false,
            pending: true
        };

        // Immediately add message to UI
        const messagesContainer = document.getElementById('messages-container');
        messagesContainer.appendChild(createMessageElement(tempMessage));
        
        // Scroll to show the new message
        scrollToBottom();

        // Send to server
        const response = await fetch('/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'text/plain'
            },
            body: content
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Update the pending message with the real data
        const pendingMessage = document.querySelector(`[data-message-id="${tempMessage.id}"]`);
        if (pendingMessage) {
            // Update message ID
            pendingMessage.dataset.messageId = result.id;
            
            // Update the timestamp
            const timestamp = pendingMessage.querySelector('.message-time');
            if (timestamp) {
                const messageDate = new Date(result.createdAt);
                timestamp.textContent = formatMessageDate(result.createdAt);
                timestamp.title = messageDate.toLocaleString();
            }
            
            // Add verification status if needed
            if (messageVerificationEnabled) {
                const meta = pendingMessage.querySelector('.message-meta');
                const verificationStatus = document.createElement('span');
                verificationStatus.className = 'verification-status';
                
                if (result.verified && result.verified.toLowerCase() === 'true') {
                    verificationStatus.title = 'Verified';
                    verificationStatus.textContent = '✓';
                } else if (result.signature) {
                    verificationStatus.title = 'Verification pending';
                    verificationStatus.textContent = '!';
                } else {
                    verificationStatus.title = 'Not verified';
                    verificationStatus.textContent = '!';
                }
                meta.appendChild(verificationStatus);
            }
        }
        
        return result;
    } catch (error) {
        console.error('Error sending message:', error);
        // Update pending message to show error
        const pendingMessage = document.querySelector(`[data-message-id="${tempMessage.id}"]`);
        if (pendingMessage) {
            const timestamp = pendingMessage.querySelector('.message-time');
            if (timestamp) {
                timestamp.textContent = 'Failed to send';
                timestamp.title = 'Message failed to send';
            }
        }
        throw error;
    }
}

async function changeUsername(newUsername) {
    try {
        // Validate username format
        if (!USERNAME_REGEX.test(newUsername)) {
            alert('Username must be 3-20 characters long and contain only letters, numbers, and underscores.');
            return false;
        }

        // Call the username change endpoint
        const response = await fetch('/change_username', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                old_username: currentUsername,
                new_username: newUsername
            })
        });

        if (!response.ok) {
            const error = await response.text();
            alert(error);
            return false;
        }

        // Update local state
        currentUsername = newUsername;
        localStorage.setItem('username', newUsername);
        
        // Update display
        const usernameDisplay = document.getElementById('username-display');
        if (usernameDisplay) {
            usernameDisplay.textContent = newUsername;
        }
        
        return true;
    } catch (error) {
        console.error('Error changing username:', error);
        alert('Failed to change username. Please try again.');
        return false;
    }
}

// Add username change UI
function setupUsernameUI() {
    // Update username display
    const usernameDisplay = document.getElementById('username-display');
    if (usernameDisplay) {
        usernameDisplay.textContent = currentUsername;
    }

    // Set up change username button click handler
    const changeButton = document.getElementById('change-username-btn');
    if (changeButton) {
        changeButton.onclick = async () => {
            const newUsername = prompt('Enter new username:');
            if (newUsername) {
                const success = await changeUsername(newUsername);
                if (!success) {
                    alert('Failed to change username. Please try a different username.');
                } else {
                    // Update display after successful change
                    if (usernameDisplay) {
                        usernameDisplay.textContent = newUsername;
                    }
                }
            }
        };
    }
}

function setupMessageInput() {
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');

    messageForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent form submission
        
        const content = messageInput.value.trim();
        if (content) {
            await sendMessage(content);
            messageInput.value = '';
        }
    });

    // Enable textarea resizing and submit on Enter (Shift+Enter for new line)
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const content = messageInput.value.trim();
            if (content) {
                sendMessage(content);
                messageInput.value = '';
            }
        }
    });
}

// Update global verification status based on all messages
function updateGlobalVerificationStatus() {
    // Only update if verification is enabled
    if (!messageVerificationEnabled) {
        const globalStatus = document.getElementById('global-verification-status');
        if (globalStatus) {
            globalStatus.style.display = 'none';
        }
        return;
    }
    
    const messages = document.querySelectorAll('.message');
    const globalStatus = document.getElementById('global-verification-status');
    
    if (!messages.length || !globalStatus) return;
    
    let allVerified = true;
    let anyVerified = false;
    
    messages.forEach(message => {
        const status = message.querySelector('.verification-status');
        if (status && status.title === 'Verified') {
            anyVerified = true;
        } else {
            allVerified = false;
        }
    });
    
    globalStatus.className = 'global-verification-status';
    
    if (allVerified) {
        globalStatus.classList.add('verified');
        globalStatus.textContent = 'Chat Verification Status: All Messages Verified';
    } else if (anyVerified) {
        globalStatus.classList.add('partial');
        globalStatus.textContent = 'Chat Verification Status: Some Messages Verified';
    } else {
        globalStatus.classList.add('unverified');
        globalStatus.textContent = 'Chat Verification Status: No Messages Verified';
    }
}

// Username validation regex - only allow alphanumeric and underscore, 3-20 chars
const USERNAME_REGEX = /^[a-zA-Z0-9_]{3,20}$/;
