// BookChat JavaScript v1.0.0 (2025-01-08T12:22:56-05:00)

const VERSION = {
    number: '1.0.0',
    timestamp: '2025-01-08T12:22:56-05:00'
};

document.addEventListener('DOMContentLoaded', function() {
    loadMessages();
    updateVersionInfo();
    // Update version age every second
    setInterval(updateVersionInfo, 1000);
});

function updateVersionInfo() {
    const versionDiv = document.getElementById('version-info');
    const now = new Date();
    const versionDate = new Date(VERSION.timestamp);
    const ageInSeconds = Math.floor((now - versionDate) / 1000);
    
    let ageText;
    if (ageInSeconds < 60) {
        ageText = `${ageInSeconds} seconds ago`;
    } else if (ageInSeconds < 3600) {
        const minutes = Math.floor(ageInSeconds / 60);
        ageText = `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
    } else {
        const hours = Math.floor(ageInSeconds / 3600);
        ageText = `${hours} hour${hours === 1 ? '' : 's'} ago`;
    }
    
    versionDiv.innerHTML = `
        <div>Version: ${VERSION.number}</div>
        <div>Built: ${ageText}</div>
        <div class="version-time">${VERSION.timestamp}</div>
    `;
}

function ensureScrollToBottom() {
    const messagesDiv = document.getElementById('messages');
    // Request an animation frame to ensure DOM is updated
    requestAnimationFrame(() => {
        // Double-check in next frame to handle any late updates
        requestAnimationFrame(() => {
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        });
    });
}

async function loadMessages() {
    try {
        const response = await fetch('/messages');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const messages = await response.json();
        const messagesDiv = document.getElementById('messages');
        messagesDiv.innerHTML = '';

        // Create document fragment for better performance
        const fragment = document.createDocumentFragment();

        messages.forEach(msg => {
            const messageElement = document.createElement('div');
            messageElement.className = 'message';
            
            // Create message header with author and signature status
            const header = document.createElement('div');
            header.className = 'message-header';
            
            const author = document.createElement('span');
            author.className = 'message-author';
            author.textContent = msg.author;
            header.appendChild(author);
            
            if (msg.signed) {
                const signatureStatus = document.createElement('span');
                signatureStatus.className = `signature-status ${msg.verified === 'true' ? 'verified' : 'unverified'}`;
                signatureStatus.title = msg.verified === 'true' ? 'Signature verified' : 'Signature could not be verified';
                signatureStatus.textContent = msg.verified === 'true' ? '✓' : '?';
                header.appendChild(signatureStatus);
            }
            
            messageElement.appendChild(header);
            
            // Add message content
            const content = document.createElement('div');
            content.className = 'message-content';
            content.textContent = msg.content;
            messageElement.appendChild(content);
            
            fragment.appendChild(messageElement);
        });

        // Batch DOM updates by using fragment
        messagesDiv.appendChild(fragment);
        ensureScrollToBottom();
    } catch (error) {
        console.error('Error loading messages:', error);
        document.getElementById('messages').innerHTML = '<p>Error loading messages</p>';
    }
}

async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (!message) return;

    try {
        const response = await fetch('/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: message })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Clear the input after successful send
        messageInput.value = '';
        
        // Reload messages
        await loadMessages();
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
    }
}

// Add event listener for Enter key in textarea
document.getElementById('message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Prevent default to avoid newline
        sendMessage();
    }
});

// Add event listener for send button
document.getElementById('send-button').addEventListener('click', sendMessage);
