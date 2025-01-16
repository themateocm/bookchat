// BookChat JavaScript (2025-01-08T12:20:30-05:00)

let currentUsername = 'anonymous';
let messageVerificationEnabled = false;

// Initialize everything
document.addEventListener('DOMContentLoaded', async () => {
    await verifyUsername();
    setupMessageInput();
    setupUsernameUI();
    await loadMessages();
});

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
        
        // Filter out unverified messages when verification is enabled
        if (messageVerificationEnabled) {
            messages = messages.filter(message => message.verified && message.verified.toLowerCase() === 'true');
        }
        
        const messagesDiv = document.getElementById('messages');
        const messagesContainer = document.getElementById('messages-container');
        messagesContainer.innerHTML = '';
        
        // Sort messages by date (newest at bottom)
        messages.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
        messages.reverse();
        
        // Add messages to container
        for (const message of messages) {
            messagesContainer.appendChild(createMessageElement(message));
        }
        
        // Scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
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

function createMessageElement(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    messageDiv.dataset.messageId = message.id;
    
    // Create message header for author and timestamp
    const messageHeader = document.createElement('div');
    messageHeader.className = 'message-header';
    
    // Create left section for author and verification status
    const leftSection = document.createElement('div');
    leftSection.className = 'header-left';
    
    // Add author name
    const authorSpan = document.createElement('span');
    authorSpan.className = 'author';
    authorSpan.textContent = message.author || 'anonymous';
    leftSection.appendChild(authorSpan);
    
    // Add verification status if enabled
    if (messageVerificationEnabled) {
        const verifiedSpan = document.createElement('span');
        verifiedSpan.className = `verification-status ${message.verified && message.verified.toLowerCase() === 'true' ? 'verified' : 'unverified'}`;
        verifiedSpan.title = message.verified && message.verified.toLowerCase() === 'true' ? 'Message signature verified' : 'Message not verified';
        verifiedSpan.innerHTML = message.verified && message.verified.toLowerCase() === 'true' ? '&#10003;' : '&#33;';
        leftSection.appendChild(verifiedSpan);
    }
    
    // Create right section for timestamp and commit hash
    const rightSection = document.createElement('div');
    rightSection.className = 'header-right';
    
    // Add timestamp
    const timestampSpan = document.createElement('span');
    timestampSpan.className = 'timestamp';
    if (message.pending) {
        timestampSpan.className += ' pending';
        timestampSpan.textContent = 'Sending...';
        timestampSpan.title = 'Message is being sent';
    } else {
        try {
            // Handle ISO 8601 dates with timezone offset
            const date = message.createdAt;
            if (date && date !== "No timestamp") {
                // Try to parse the date, handling both ISO 8601 and other formats
                try {
                    // First try to parse as ISO 8601
                    const messageDate = new Date(date);
                    if (!isNaN(messageDate.getTime())) {
                        const options = { hour: '2-digit', minute: '2-digit' };
                        timestampSpan.textContent = messageDate.toLocaleTimeString([], options);
                        timestampSpan.title = messageDate.toLocaleString();
                    } else {
                        // If not a valid date, just display the raw string
                        timestampSpan.textContent = date;
                        timestampSpan.title = date;
                    }
                } catch (error) {
                    console.error('Error parsing date:', error, date);
                    timestampSpan.textContent = date;
                    timestampSpan.title = 'Error parsing date';
                }
            } else {
                timestampSpan.textContent = date || 'Unknown time';
                timestampSpan.title = date || 'Unknown time';
            }
        } catch (error) {
            console.error('Error formatting date:', error, message.createdAt);
            timestampSpan.textContent = message.createdAt || 'Invalid date';
            timestampSpan.title = 'Error parsing date';
        }
    }
    rightSection.appendChild(timestampSpan);
    
    // Add commit hash with GitHub link if available
    if (message.commit_hash && message.repo_name) {
        const commitSpan = document.createElement('span');
        commitSpan.className = 'commit-hash';
        const commitLink = document.createElement('a');
        commitLink.href = `https://github.com/${message.repo_name}/commit/${message.commit_hash}`;
        commitLink.target = '_blank';
        commitLink.textContent = message.commit_hash;
        commitLink.title = 'View commit on GitHub';
        commitSpan.appendChild(commitLink);
        rightSection.appendChild(commitSpan);
    }
    
    // Add source file link if available and verification is enabled and not pending
    if (message.file && messageVerificationEnabled && !message.pending) {
        const sourceLink = document.createElement('a');
        sourceLink.className = 'source-link';
        sourceLink.href = `/messages/${message.file.split('/').pop()}`; // Get just the filename
        sourceLink.textContent = '&#128273;';
        sourceLink.title = 'View message source file';
        sourceLink.target = '_blank'; // Open in new tab
        rightSection.appendChild(sourceLink);
    }
    
    messageHeader.appendChild(leftSection);
    messageHeader.appendChild(rightSection);
    messageDiv.appendChild(messageHeader);
    
    // Add message content
    const content = document.createElement('div');
    content.className = 'content';
    // Ensure we display the actual message content, not metadata
    content.textContent = message.content || 'No message content';
    messageDiv.appendChild(content);
    
    return messageDiv;
}

async function sendMessage(content, type = 'message') {
    try {
        // Ensure content is a string and trim it
        content = String(content || '').trim();
        console.log('sendMessage called with content:', content, 'Length:', content.length);
        console.log('Content type:', typeof content);
        
        if (!content) {
            console.error('Empty message content in sendMessage');
            return;
        }

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
        
        // Scroll to bottom
        const messagesDiv = document.getElementById('messages');
        messagesDiv.scrollTop = messagesDiv.scrollHeight;

        // Create request body and log it
        const requestBody = {
            content: content,
            username: currentUsername
        };
        console.log('Request body before stringify:', requestBody);
        const stringifiedBody = JSON.stringify(requestBody);
        console.log('Stringified request body:', stringifiedBody);
        
        const response = await fetch('/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: stringifiedBody
        });
        
        // Log response status
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Server error response:', errorText);
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }
        
        const result = await response.json();
        
        // Update the pending message with the real data
        const pendingMessage = document.querySelector(`[data-message-id="${tempMessage.id}"]`);
        if (pendingMessage && result.data) {
            // Update message ID and data
            pendingMessage.dataset.messageId = result.data.id || tempMessage.id;
            
            // Update the timestamp
            const timestamp = pendingMessage.querySelector('.timestamp');
            if (timestamp && result.data.createdAt) {
                try {
                    const messageDate = new Date(result.data.createdAt);
                    const options = { hour: '2-digit', minute: '2-digit' };
                    timestamp.textContent = messageDate.toLocaleTimeString([], options);
                    timestamp.title = messageDate.toLocaleString();
                    timestamp.classList.remove('pending');
                } catch (error) {
                    console.error('Error updating timestamp:', error);
                    timestamp.textContent = 'Unknown time';
                    timestamp.title = 'Error parsing date';
                }
            }
            
            // Add verification status if needed
            if (messageVerificationEnabled) {
                const leftSection = pendingMessage.querySelector('.header-left');
                const verificationStatus = document.createElement('span');
                verificationStatus.className = 'verification-status';
                
                if (result.data.verified && result.data.verified.toLowerCase() === 'true') {
                    verificationStatus.className += ' verified';
                    verificationStatus.title = 'Message verified';
                    verificationStatus.innerHTML = '&#10003;';
                } else {
                    verificationStatus.className += ' unverified';
                    verificationStatus.title = 'Message not verified';
                    verificationStatus.innerHTML = '&#33;';
                }
                leftSection.insertBefore(verificationStatus, leftSection.firstChild);
            }
        }
        
        return result;
    } catch (error) {
        console.error('Error sending message:', error);
        // Update pending message to show error
        const pendingMessage = document.querySelector(`[data-message-id="${tempMessage.id}"]`);
        if (pendingMessage) {
            const timestamp = pendingMessage.querySelector('.timestamp');
            if (timestamp) {
                timestamp.className = 'timestamp error';
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
    // Hide no-JS form and show JS form
    const noJsForm = document.getElementById('message-form');
    const jsForm = document.getElementById('js-message-form');
    if (noJsForm && jsForm) {
        noJsForm.style.display = 'none';
        jsForm.style.display = 'flex';
    }
    
    const messageForm = document.getElementById('js-message-form');
    const messageInput = document.getElementById('message-input');
    const charCounter = document.getElementById('char-counter');

    // Update character count
    function updateCharCount() {
        const count = messageInput.value.length;
        charCounter.textContent = `${count} character${count !== 1 ? 's' : ''}`;
    }

    // Add input event listener for character counting
    messageInput.addEventListener('input', updateCharCount);

    messageForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const content = messageInput.value.trim();
        if (content) {
            await sendMessage(content);
            messageInput.value = '';
            updateCharCount(); // Reset counter after sending
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
                updateCharCount(); // Reset counter after sending
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
        if (status && status.classList.contains('verified')) {
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
