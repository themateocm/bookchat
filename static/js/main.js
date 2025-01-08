// Main JavaScript for BookChat

document.addEventListener('DOMContentLoaded', function() {
    // Clear the "Loading messages..." text when the page loads
    document.getElementById('messages').innerHTML = '';
    loadMessages();
});

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
        
        // Reload messages to show the new one
        await loadMessages();
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
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
        messagesDiv.innerHTML = '';

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
            
            messagesDiv.appendChild(messageElement);
        });
    } catch (error) {
        console.error('Error loading messages:', error);
        document.getElementById('messages').innerHTML = '<p>Error loading messages</p>';
    }
}

// Add event listener for Enter key in textarea
document.getElementById('message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Prevent default to avoid newline
        sendMessage();
    }
});
