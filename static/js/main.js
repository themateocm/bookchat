// BookChat JavaScript (2025-01-08T12:20:30-05:00)

document.addEventListener('DOMContentLoaded', function() {
    loadMessages();
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
            const messageElement = document.createElement('div');
            messageElement.className = 'message';
            
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
            
            const content = document.createElement('div');
            content.className = 'message-content';
            content.textContent = msg.content;
            messageElement.appendChild(content);
            
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

        messageInput.value = '';
        await loadMessages();
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
    }
}

document.getElementById('message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

document.getElementById('send-button').addEventListener('click', sendMessage);
