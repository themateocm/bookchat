Create a secure, Git-backed chat application called BookChat with the following specifications:

1. Core Features:
- Web-based messaging interface with real-time updates
- Git-based message storage with optional GitHub synchronization
- RSA signature verification for message authenticity
- Support for message threading and username changes
- No external web frameworks - use Python's built-in http.server

2. Technical Requirements:
- Backend: Python with minimal dependencies (http.server, cryptography)
- Frontend: Vanilla HTML/CSS/JavaScript
- Storage: Git-based with JSON message files
- Security: RSA key pairs for message signing/verification
- Optional GitHub integration for message persistence

3. Message Structure:
- Store messages as individual files in messages/ directory
- Filename format: YYYYMMDD_HHMMSS_username.txt
- Message format:
  ```
  message_content

  -- 
  Author: username
  Date: YYYY-MM-DDTHH:mm:ss.SSSSSS
  Public-Key: identity/public_keys/username.pub
  Parent-Message: YYYYMMDD_HHMMSS_username.txt  # Optional
  Signature: hex_encoded_signature  # Optional
  Type: message|username_change|system|error  # Optional
  ```

4. Key Components:
a) Server (server.py):
- HTTP request handler for message endpoints
- Static file serving for web interface
- Message verification and storage logic

b) Git Manager (git_manager.py):
- Handle Git operations (commit, push)
- Message file management
- GitHub API integration (optional)

c) Key Manager:
- RSA key pair generation and management
- Message signing and verification
- Public key distribution

5. Directory Structure:
```
bookchat/
├── server.py
├── git_manager.py
├── static/
│   ├── css/style.css
│   └── js/main.js
├── templates/
│   └── index.html
├── messages/
├── keys/
│   └── local.pem
└── identity/
    └── public_keys/
```

6. Environment Configuration (.env):
```
# GitHub Configuration (optional)
SYNC_TO_GITHUB=false
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=username/repository

# Logging Configuration
BOOKCHAT_DEBUG=true  # Optional, enables debug logging

# Server Configuration
PORT=8000

# Key Management
KEYS_DIR=/path/to/keys  # Optional, default: repo/keys
SIGN_MESSAGES=true  # Optional, default: true

# Security
MESSAGE_VERIFICATION=false  # Optional, default: false
```

7. Security Features:
- RSA signature verification for all user messages
- Secure key storage and management
- Optional message verification toggle
- Public key distribution for verification

8. API Endpoints:
- GET / : Serve main chat interface
- GET /messages : Retrieve all messages
- POST /messages : Create new message
- GET /verify_username : Verify current username

The application should provide a clean, minimalist web interface that allows users to:
- Send and receive messages in real-time
- View message history
- Change usernames (with signature verification)
- See message timestamps and authors
- Follow message threads

Ensure proper error handling, logging, and security measures throughout the implementation. The application should work standalone with local Git storage and optionally sync with GitHub when configured.
