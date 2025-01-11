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
        
        const messages = await response.json();
        const messagesDiv = document.getElementById('messages');
        const messagesContainer = document.getElementById('messages-container');
        messagesContainer.innerHTML = '';
        
        // Sort messages by date (newest at bottom)
        messages.sort((a, b) => new Date(b.date) - new Date(a.date));
        messages.reverse();
        
        // Track username changes and errors
        let currentUsername = 'anonymous';
        for (const message of messages) {
            if (message.type === 'username_change' && message.verified === 'true') {
                try {
                    const content = JSON.parse(message.content);
                    if (content.old_username === currentUsername) {
                        currentUsername = content.new_username;
                    }
                } catch (e) {
                    console.error('Failed to parse username change:', e);
                }
            }
            messagesContainer.appendChild(createMessageElement(message));
        }
        
        // Update current username display
        const usernameDisplay = document.getElementById('current-username');
        if (usernameDisplay) {
            usernameDisplay.textContent = `Current username: ${currentUsername}`;
        }
        
        // Scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

function createMessageElement(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    messageDiv.dataset.messageId = message.id;
    
    // Add author info
    const authorSpan = document.createElement('span');
    authorSpan.className = 'author';
    authorSpan.textContent = message.author;
    if (message.verified === 'true') {
        authorSpan.classList.add('verified');
        authorSpan.title = 'Verified message';
    }
    messageDiv.appendChild(authorSpan);
    
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
    
    return messageDiv;
}

async function sendMessage(content, type = 'message') {
    try {
        const response = await fetch('/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content,
                type,
                author: currentUsername
            })
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
        
        // First verify if username exists
        const messages = await fetch('/messages').then(r => r.json());
        const existingChange = messages.find(m => 
            m.type === 'username_change' && 
            JSON.parse(m.content).new_username === newUsername
        );
        
        if (existingChange) {
            alert('This username is already taken. Please choose another one.');
            return false;
        }
        
        // Proceed with username change
        const content = JSON.stringify({
            old_username: currentUsername,
            new_username: newUsername
        });
        
        const success = await sendMessage(content, 'username_change');
        if (success) {
            currentUsername = newUsername;
            localStorage.setItem('username', newUsername);
            
            // Update display
            const usernameDisplay = document.getElementById('current-username');
            if (usernameDisplay) {
                usernameDisplay.textContent = `Current username: ${newUsername}`;
            }
            
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error changing username:', error);
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
