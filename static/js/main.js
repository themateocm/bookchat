// BookChat JavaScript (2025-01-08T12:20:30-05:00)

document.addEventListener('DOMContentLoaded', async () => {
    setupMessageInput();
    setupUsernameUI();
    await loadMessages();
});

async function loadMessages() {
    try {
        const response = await fetch('/messages');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const messages = await response.json();
        const messagesDiv = document.getElementById('messages');
        
        // Clear messages
        messagesDiv.innerHTML = '';
        
        // Create messages container that will hold all messages
        const messagesContainer = document.createElement('div');
        messagesContainer.className = 'messages-container';
        messagesContainer.style.marginTop = 'auto'; // Push messages to bottom initially

        messages.forEach(msg => {
            const messageElement = createMessageElement(msg);
            messagesContainer.appendChild(messageElement);
        });

        // Add all messages at once
        messagesDiv.appendChild(messagesContainer);
        
        // Scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    } catch (error) {
        console.error('Error loading messages:', error);
        document.getElementById('messages').innerHTML = '<p>Error loading messages</p>';
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
    
    // Handle system messages differently
    if (message.type === 'error') {
        contentDiv.classList.add('error');
    } else if (message.type === 'system') {
        contentDiv.classList.add('system');
    }
    
    contentDiv.textContent = message.content;
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
                author: currentUsername || 'anonymous'
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

let currentUsername = 'anonymous';

async function changeUsername(newUsername) {
    if (!newUsername || newUsername === currentUsername) {
        return false;
    }
    
    try {
        // Send username change request as a special message
        const result = await sendMessage(JSON.stringify({
            new_username: newUsername,
            old_username: currentUsername
        }), 'username_change');
        
        // Wait a bit for the change to process
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Refresh messages to see the result
        await loadMessages();
        
        // Update current username if no error message was received
        const messages = document.querySelectorAll('.message');
        const lastMessage = messages[messages.length - 1];
        if (lastMessage && lastMessage.querySelector('.content.error')) {
            return false;
        }
        
        currentUsername = newUsername;
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
            if (success) {
                usernameDisplay.textContent = `Current username: ${currentUsername}`;
            }
        }
    };
    
    header.appendChild(usernameDisplay);
    header.appendChild(changeButton);
    
    const chat = document.getElementById('chat');
    chat.parentNode.insertBefore(header, chat);
}

function setupMessageInput() {
    document.getElementById('message-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(document.getElementById('message-input').value.trim());
        }
    });

    document.getElementById('send-button').addEventListener('click', () => {
        sendMessage(document.getElementById('message-input').value.trim());
    });
}
