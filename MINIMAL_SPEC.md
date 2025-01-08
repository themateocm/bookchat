# BookChat Minimal Implementation Spec

Create a secure chat system with message signing and username management. Messages are stored as text files, and usernames are verified cryptographically.

## Core Requirements

### Message Storage
- Store each message as a text file: `YYYYMMDD_HHMMSS_username.txt`
- Message format:
  ```
  Date: ISO-8601 timestamp
  Author: username
  Type: message|username_change|system|error
  [Signature: hex_encoded_signature]

  message content
  ```

### Security
- Each user has RSA public/private keypair
- Store public keys as `public_keys/username.pub`
- Sign messages with private key
- Verify username changes with signatures

### API Endpoints
```
GET /messages
  Returns: Array of message objects

POST /messages
  Body: { content, type, author }
  Signs and saves message

GET /verify_username
  Returns: Current verified username
```

### Username Changes
1. Client sends username change message:
   ```json
   {
     "type": "username_change",
     "content": {
       "old_username": "old",
       "new_username": "new"
     }
   }
   ```
2. Server verifies signature with old username's public key
3. Moves public key file to new username
4. Returns success/error

### Validation
- Usernames: `/^[a-zA-Z0-9_]{3,20}$/`
- Required message fields: date, author, type, content
- Valid message types: message, username_change, system, error

## Example Message File
```
Date: 2025-01-08T13:52:18-05:00
Author: alice
Type: message
Signature: a1b2c3...

Hello, world!
```

## Frontend Implementation

### HTML Structure
```html
<!DOCTYPE html>
<html>
<head>
    <title>BookChat</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <noscript>
        <link rel="stylesheet" href="/static/css/noscript.css">
    </noscript>
</head>
<body>
    <div class="container">
        <div class="header">
            <span id="current-username">Current username: anonymous</span>
            <!-- No-JS username form -->
            <form method="POST" action="/username" class="nojs-only">
                <input name="new_username" required>
                <button type="submit">Change Username</button>
            </form>
            <!-- JS-only button -->
            <button id="change-username-btn" class="js-only">Change Username</button>
        </div>
        
        <div id="messages">
            <!-- No-JS refresh -->
            <form method="GET" action="/" class="nojs-only">
                <button type="submit">Refresh</button>
            </form>
            <div id="messages-container"></div>
        </div>
        
        <!-- Message form works with/without JS -->
        <form method="POST" action="/messages" class="message-form">
            <textarea name="content" required></textarea>
            <button type="submit">Send</button>
        </form>
    </div>
    <script src="/static/js/main.js"></script>
</body>
</html>
```

### JavaScript Core Functions
```javascript
// Core state
let currentUsername = 'anonymous';

// Main functions
async function loadMessages() {
    const messages = await fetch('/messages').then(r => r.json());
    displayMessages(messages);
}

async function sendMessage(content, type = 'message') {
    await fetch('/messages', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ content, type, author: currentUsername })
    });
    await loadMessages();
}

async function changeUsername(newUsername) {
    if (!/^[a-zA-Z0-9_]{3,20}$/.test(newUsername)) return false;
    const content = JSON.stringify({
        old_username: currentUsername,
        new_username: newUsername
    });
    const success = await sendMessage(content, 'username_change');
    if (success) {
        currentUsername = newUsername;
        localStorage.setItem('username', newUsername);
    }
    return success;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadMessages();
    setupEventListeners();
});
```

## Python Server Implementation

### Core Classes
```python
class KeyManager:
    def __init__(self, keys_dir):
        self.keys_dir = Path(keys_dir)
        self.private_key_path = self.keys_dir / 'local.pem'
        self.public_key_path = self.keys_dir / 'local.pub'
        self._ensure_keypair()
    
    def sign_message(self, message):
        return subprocess.run(
            ['openssl', 'dgst', '-sha256', '-sign', str(self.private_key_path)],
            input=message.encode(),
            capture_output=True
        ).stdout.hex()
    
    def verify_signature(self, message, signature_hex, public_key_pem):
        # Convert hex signature to bytes and verify with OpenSSL
        return self._verify_with_openssl(message, signature_hex, public_key_pem)

class MessageManager:
    def __init__(self, messages_dir, key_manager):
        self.messages_dir = Path(messages_dir)
        self.key_manager = key_manager
    
    def save_message(self, content, author, type='message'):
        timestamp = datetime.now().isoformat()
        filename = f"{timestamp:%Y%m%d_%H%M%S}_{author}.txt"
        signature = self.key_manager.sign_message(content)
        
        message = f"""Date: {timestamp}
Author: {author}
Type: {type}
Signature: {signature}

{content}"""
        
        (self.messages_dir / filename).write_text(message)
        return filename
    
    def read_messages(self):
        messages = []
        for file in sorted(self.messages_dir.glob('*.txt')):
            content = file.read_text()
            messages.append(self._parse_message(content))
        return messages

class ChatServer(HTTPServer):
    def __init__(self, messages_dir, keys_dir):
        self.message_manager = MessageManager(messages_dir, KeyManager(keys_dir))
        super().__init__(('', 8000), ChatRequestHandler)
```

### Request Handler
```python
class ChatRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/messages':
            self._send_json(self.server.message_manager.read_messages())
        elif self.path == '/verify_username':
            self._send_json(self._verify_username())
        else:
            super().do_GET()  # Serve static files
    
    def do_POST(self):
        content_len = int(self.headers['Content-Length'])
        body = self.rfile.read(content_len).decode()
        
        if self.path == '/messages':
            if self.headers.get('Content-Type') == 'application/json':
                data = json.loads(body)
            else:
                data = parse_qs(body)
                data = {
                    'content': data.get('content', [''])[0],
                    'author': 'anonymous',
                    'type': 'message'
                }
            
            filename = self.server.message_manager.save_message(**data)
            self._send_json({'status': 'success', 'id': filename})
```

## Implementation Notes
1. Default to 'anonymous' user if no username set
2. Verify signatures before username changes
3. Sort messages by timestamp when displaying
4. Sanitize all user inputs
5. Handle both JSON and form-data POST requests
