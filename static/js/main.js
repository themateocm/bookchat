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
        const messagesContainer = document.createElement('div');
        messagesContainer.id = 'messages-container';
        messagesDiv.innerHTML = '';
        messagesDiv.appendChild(messagesContainer);

        messages.forEach(msg => {
            const messageElement = createMessageElement(msg);
            messagesContainer.appendChild(messageElement);
        });

        // Scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
    } catch (error) {
        console.error('Error loading messages:', error);
        const messagesDiv = document.getElementById('messages');
        messagesDiv.innerHTML = '<p class="error">Error loading messages. Please try again later.</p>';
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
        return result;
    } catch (error) {
        console.error('Error sending message:', error);
        throw error;
    }
}

async function changeUsername(newUsername) {
    // Clean and validate the new username
    newUsername = newUsername.trim();
    
    if (!newUsername) {
        return false;
    }
    
    // If it's the same username, just return success
    if (newUsername === currentUsername) {
        return true;
    }
    
    try {
        // Send username change request as a special message
        const result = await sendMessage(JSON.stringify({
            new_username: newUsername,
            old_username: currentUsername
        }), 'username_change');
        
        // Wait a bit for the change to process
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Verify the username change with the server
        const verified = await verifyUsername();
        if (!verified) {
            return false;
        }
        
        // Refresh messages to show the change
        await loadMessages();
        return true;
    } catch (error) {
        console.error('Error changing username:', error);
        return false;
    }
}

// Add username change UI
function setupUsernameUI() {
    const header = document.createElement('div');
    header.className = 'header';
    
    const usernameDisplay = document.createElement('span');
    usernameDisplay.textContent = `Current username: ${currentUsername}`;
    usernameDisplay.id = 'current-username';
    
    const changeButton = document.createElement('button');
    changeButton.textContent = 'Change Username';
    changeButton.onclick = async () => {
        const newUsername = prompt('Enter new username:');
        if (newUsername) {
            const success = await changeUsername(newUsername);
            if (!success) {
                alert('Failed to change username. Please try a different username.');
            }
        }
    };
    
    header.appendChild(usernameDisplay);
    header.appendChild(changeButton);
    
    const container = document.querySelector('.container');
    container.insertBefore(header, container.firstChild);
}

function setupMessageInput() {
    const messageInput = document.getElementById('message-input');
    
    async function sendAndClear() {
        const content = messageInput.value.trim();
        if (content) {
            try {
                await sendMessage(content);
                messageInput.value = '';
                await loadMessages();
                // Ensure scroll to bottom after sending
                const messagesDiv = document.getElementById('messages');
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            } catch (error) {
                console.error('Failed to send message:', error);
            }
        }
    }
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendAndClear();
        }
    });

    document.getElementById('send-button').addEventListener('click', sendAndClear);
}
