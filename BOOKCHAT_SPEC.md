# BookChat Application Specification

## Overview
BookChat is a secure, signature-verified chat application that uses Git for message storage and RSA signatures for message verification. Users can send messages and change usernames with cryptographic verification. The application optionally supports GitHub synchronization for message persistence.

## Core Components

### 1. Message Storage
- Messages are stored in a Git repository
- Each message is a separate `.txt` file in `messages/` directory
- Message filenames follow the format: `YYYYMMDD_HHMMSS_username.txt`
- Public keys are stored in `public_keys/` directory as `{username}.pub`

### 2. Message Format
Messages are stored as text files with the following format:
```
Date: YYYY-MM-DDTHH:mm:ss.SSSSSS
Author: username
Parent-Message: YYYYMMDD_HHMMSS_username.txt  # Optional, used for threaded messages
Signature: base64_encoded_signature
Type: message|username_change|system|error

message_content
```

The message content format depends on the type:
1. Regular message: Plain text
2. Username change: JSON object `{"old_username": "old", "new_username": "new"}`
3. System message: Plain text system notification
4. Error message: Plain text error description

### 3. Message Types
1. **Regular Message** (`Type: message`)
   - Normal chat messages
   - Content is plain text
   - Must be signed by author

2. **Username Change** (`Type: username_change`)
   - Content is JSON: `{"old_username": "old", "new_username": "new"}`
   - Must be signed by old username
   - Moves public key file from old to new username

3. **System Message** (`Type: system`)
   - System notifications
   - No signature required
   - Author is "system"

4. **Error Message** (`Type: error`)
   - Error notifications
   - No signature required
   - Author is "system"

### 4. API Endpoints

#### GET /
- Serves the main chat interface
- Returns: HTML page

#### GET /messages
- Retrieves all messages
- Returns: JSON array of messages

#### POST /messages
- Creates a new message
- Body: 
  ```json
  {
    "content": "message text",
    "type": "message|username_change|system|error",
    "author": "username"
  }
  ```
- Returns: JSON message object

#### GET /verify_username
- Verifies current username from message history
- Returns:
  ```json
  {
    "username": "username",
    "status": "verified|default"
  }
  ```

### 5. Security

#### Key Management
The application uses a dedicated KeyManager class for RSA operations:
```python
class KeyManager:
    def __init__(self, keys_dir)  # Initialize key manager and generate keys if needed
    def sign_message(self, message)  # Sign message with private key
    def verify_signature(self, message, signature_hex, public_key_pem)  # Verify message signature
    def export_public_key(self, path)  # Export public key to specified path
```

#### RSA Key Pair
- Each user has an RSA key pair
- Private key stored locally as `keys/local.pem`
- Public key stored in repo as `public_keys/{username}.pub`
- Key format: PEM
- Key size: 2048 bits
- Keys are generated using OpenSSL

#### Message Signing
1. Create signature:
   - Sign message JSON (excluding signature field)
   - Use SHA256 for hashing
   - Base64 encode the signature

2. Verify signature:
   - Load author's public key
   - Verify signature against message JSON
   - Set verified=true if valid

### 6. Username Management

#### Client-Side Storage
- Username is stored in browser's localStorage
- On page load, client verifies username with server
- If server is unreachable, falls back to stored username
- If no stored username, defaults to 'anonymous'

#### Username Change Process
1. Client requests username change with signed message
2. Server verifies:
   - Message is signed by old username
   - New username doesn't exist
   - Public key exists for old username
3. Server moves public key file
4. Client updates:
   - Local storage
   - UI display
   - Current session state

#### Username Verification
1. Server checks message history for username changes
2. Verifies public key exists
3. Returns verified username or 'anonymous'

### 7. GitHub Integration

The application optionally supports GitHub synchronization for message persistence:

#### Configuration
Environment variables control GitHub integration:
```shell
GITHUB_TOKEN=your_github_token
GITHUB_REPO=username/repo
SYNC_TO_GITHUB=true|false
```

#### GitManager GitHub Features
```python
class GitManager:
    def __init__(self, repo_path)  # Initialize with GitHub credentials
    def init_git_repo(self)  # Set up Git repository
    def ensure_repo_exists(self)  # Clone from GitHub if needed
    def sync_changes_to_github(self, filepath, author)  # Push changes to GitHub
```

#### Synchronization Process
1. On startup:
   - Check if GitHub sync is enabled
   - Clone repository if it doesn't exist
   - Initialize Git repository if needed

2. On message save:
   - Save message locally
   - If GitHub sync enabled:
     - Commit changes
     - Push to remote repository

3. On public key changes:
   - Save key locally
   - If GitHub sync enabled:
     - Commit and push changes

## Client-Side Implementation

### Required JavaScript Functions

```javascript
// Initialize
async function verifyUsername()
async function loadMessages()
async function sendMessage(content, type = 'message')
async function changeUsername(newUsername)

// UI Components
function setupUsernameUI()
function setupMessageInput()
function createMessageElement(message)
```

### Required CSS Components

```css
/* Core layout */
.container
#messages
#messages-container
.message-form

/* Message styling */
.message
.message .author
.message .content
.message .content.username-change
.message .content.error
.message .content.system

/* Input styling */
.message-input-container
#message-input
#send-button
```

## Server-Side Implementation

### Required Python Classes

```python
class GitManager:
    def __init__(self, repo_path)
    def read_message(self, message_id)  # message_id is the filename without .txt
    def save_message(self, content, author, type='message')  # Creates timestamp and saves .txt file
    def handle_username_change(self, old_username, new_username, message_id)
    def verify_signature(self, message, signature, username)
    def format_message(self, date, author, content, type, parent=None)  # Creates message text format

class ChatRequestHandler(SimpleHTTPRequestHandler):
    def do_GET()
    def do_POST()
    def serve_messages()  # Returns messages as JSON array for client
    def verify_username()
    def parse_message(self, message_text)  # Parses .txt format into dict
```

## File Structure
```
bookchat/
├── server.py              # HTTP server
├── git_manager.py         # Git and message management
├── templates/
│   └── index.html        # Main chat interface
├── static/
│   ├── css/
│   │   └── style.css     # Styles
│   └── js/
│       └── main.js       # Client-side logic
├── messages/             # Message storage (.txt files)
│   ├── YYYYMMDD_HHMMSS_username.txt  # Message files
│   └── .gitkeep
├── public_keys/          # User public keys
│   └── username.pub      # RSA public keys
└── keys/                 # Local private key
    └── local.pem         # RSA private key
```

## Message Examples

### Regular Message
```
Date: 2025-01-08T13:01:31.611858
Author: alice
Signature: base64_encoded_signature
Type: message

Hello, this is a test message!
```

### Username Change Message
```
Date: 2025-01-08T13:01:31.611858
Author: alice
Signature: base64_encoded_signature
Type: username_change

{"old_username": "alice", "new_username": "alice2"}
```

### System Message
```
Date: 2025-01-08T13:03:08.879653
Author: system
Parent-Message: 20250108_130308_anonymous.txt
Signature: base64_encoded_signature
Type: error

Username change failed: New username already exists
```

## Dependencies
- Python 3.8+
- OpenSSL for RSA operations
- Git for message storage
- Modern web browser with JavaScript enabled

## Security Considerations
1. Never expose private keys
2. Verify all signatures before accepting messages
3. Validate username changes cryptographically
4. Protect against replay attacks
5. Validate message format and content
6. Ensure proper line endings in message files

## Implementation Notes
1. All timestamps must be in ISO format with microseconds
2. Message filenames must match their Date field
3. Username changes must be atomic
4. Public keys must be unique per username
5. Messages must be properly formatted text files
6. Parent-Message is optional and used for threading
7. System messages should use "system" as author
