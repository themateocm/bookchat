// BookChat JavaScript (2025-01-08T12:20:30-05:00)

let currentUsername = 'anonymous';

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
        const messages = data.messages;
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
    
    // Add author info
    const authorSpan = document.createElement('span');
    authorSpan.className = 'author';
    authorSpan.textContent = message.author || 'anonymous';
    if (message.verified === 'true') {
        authorSpan.classList.add('verified');
        authorSpan.title = 'Verified message';
    }
    if (message.signature) {
        authorSpan.classList.add('signed');
    }
    messageHeader.appendChild(authorSpan);
    
    // Add public key link if available
    if (message.public_key) {
        const keyLink = document.createElement('a');
        keyLink.className = 'key-link';
        keyLink.href = `/${message.public_key}`; // Link to the public key file
        keyLink.textContent = '🔑';
        keyLink.title = `View ${message.author}'s public key`;
        keyLink.target = '_blank'; // Open in new tab
        messageHeader.appendChild(keyLink);
    }
    
    // Add timestamp
    const timestamp = document.createElement('span');
    timestamp.className = 'timestamp';
    const messageDate = new Date(message.createdAt);
    timestamp.textContent = messageDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    timestamp.title = messageDate.toLocaleString();
    messageHeader.appendChild(timestamp);
    
    // Add source file link if available
    if (message.file) {
        const sourceLink = document.createElement('a');
        sourceLink.className = 'source-link';
        sourceLink.href = `/messages/${message.file.split('/').pop()}`; // Get just the filename
        sourceLink.textContent = '📄';
        sourceLink.title = 'View source file';
        sourceLink.target = '_blank'; // Open in new tab
        messageHeader.appendChild(sourceLink);
    }
    
    messageDiv.appendChild(messageHeader);
    
    // Add message content
    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';
    
    // Handle different message types
    if (message.type === 'error') {
        contentDiv.classList.add('error');
        contentDiv.textContent = message.content;
    } else if (message.type === 'system') {
        contentDiv.classList.add('system');
        contentDiv.textContent = message.content;
    } else if (message.type === 'username_change') {
        contentDiv.classList.add('username-change');
        try {
            const data = JSON.parse(message.content);
            contentDiv.innerHTML = `
                <div class="username-change-icon">👤</div>
                <div class="username-change-text">
                    Changed username from <span class="old-username">${data.old_username}</span> 
                    to <span class="new-username">${data.new_username}</span>
                </div>
            `;
        } catch (e) {
            contentDiv.textContent = message.content;
        }
    } else {
        contentDiv.textContent = message.content;
    }
    
    messageDiv.appendChild(contentDiv);
    
    // Add signature if present
    if (message.signature) {
        const signatureDiv = document.createElement('div');
        signatureDiv.className = 'signature';
        
        const signatureIcon = document.createElement('span');
        signatureIcon.className = 'signature-icon';
        signatureIcon.textContent = '🔒';
        signatureDiv.appendChild(signatureIcon);
        
        const signatureText = document.createElement('div');
        signatureText.className = 'signature-text';
        
        const signedText = document.createElement('span');
        signedText.className = message.verified ? 'signature-verified' : 'signature-unverified';
        signedText.textContent = message.verified ? 'Verified' : 'Unverified';
        signatureText.appendChild(signedText);
        
        const signedMessage = document.createElement('span');
        signedMessage.textContent = 'Signed Message';
        signatureText.appendChild(signedMessage);
        
        signatureDiv.appendChild(signatureText);
        messageDiv.appendChild(signatureDiv);
    }
    
    return messageDiv;
}

async function sendMessage(content, type = 'message') {
    try {
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
        
        // Reload messages to show the new message
        await loadMessages();
        
        return result;
    } catch (error) {
        console.error('Error sending message:', error);
        throw error;
    }
}

// Username validation regex - only allow alphanumeric and underscore, 3-20 chars
const USERNAME_REGEX = /^[a-zA-Z0-9_]{3,20}$/;

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
        const usernameDisplay = document.getElementById('current-username');
        if (usernameDisplay) {
            usernameDisplay.textContent = `Current username: ${newUsername}`;
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
    // Set up change username button click handler
    const changeButton = document.getElementById('change-username-btn');
    if (changeButton) {
        changeButton.onclick = async () => {
            const newUsername = prompt('Enter new username:');
            if (newUsername) {
                const success = await changeUsername(newUsername);
                if (!success) {
                    alert('Failed to change username. Please try a different username.');
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
    
    if (messageForm && messageInput) {
        // Handle form submit (for button click)
        messageForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const content = messageInput.value.trim();
            if (content) {
                try {
                    await sendMessage(content);
                    messageInput.value = '';
                } catch (error) {
                    console.error('Failed to send message:', error);
                    alert('Failed to send message. Please try again.');
                }
            }
        });

        // Handle Enter key press
        messageInput.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const content = messageInput.value.trim();
                if (content) {
                    try {
                        await sendMessage(content);
                        messageInput.value = '';
                    } catch (error) {
                        console.error('Failed to send message:', error);
                        alert('Failed to send message. Please try again.');
                    }
                }
            }
        });
    }
}
