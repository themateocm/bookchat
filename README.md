# BookChat - Git-Backed Messaging Application

A lightweight, Git-backed web-based messaging application that allows users to communicate through a simple interface while maintaining message history in a Git repository.

## Features

- Simple and intuitive web interface
- Flexible storage backend using Git
- Git integration for message history
- Real-time message updates
- Basic user authentication
- Markdown support for messages
- Serverless-friendly when using Git storage
- Comprehensive logging system with multiple debug levels

## Tech Stack

- Backend: Python (No frameworks)
- Storage: Git-based JSON files
- Frontend: HTML, CSS, JavaScript (Vanilla)
- Version Control: Git (via GitHub API)
- Authentication: GitHub OAuth

## Project Structure

```
bookchat/
├── README.md
├── .env
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   ├── index.html
│   └── login.html
├── storage/
│   ├── __init__.py
│   ├── factory.py
│   └── git_storage.py
├── server.py
└── requirements.txt
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bookchat.git
   cd bookchat
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure storage backend in `.env`:
   ```bash
   # Required settings
   GITHUB_TOKEN=your_github_token
   GITHUB_REPO=username/repo

   # Optional settings
   PORT=8000             # Default: 8000
   REPO_PATH=/path/to/repo  # Default: current directory
   SYNC_TO_GITHUB=true   # Default: false
   ```

5. Run the server:
   ```bash
   python server.py
   ```

## Deployment Options

BookChat supports multiple deployment options:

### 1. GitHub Pages (Serverless)
- Use Git storage backend
- Host static files on GitHub Pages
- Messages stored directly in the Git repository
- Perfect for small to medium-sized deployments

### 2. Traditional Server
- Use Git storage
- Deploy on any Python-compatible hosting platform
- Suitable for larger deployments with more control

### 3. Serverless Platforms
- Use Git storage backend
- Deploy on platforms like Vercel, Netlify, or Cloudflare Pages
- Great for scalable, maintenance-free deployments

## Logging and Debugging

BookChat includes a comprehensive logging system with multiple debug levels:

### Log Files

All logs are stored in the `logs` directory:
- `logs/debug.log`: Contains all log messages (DEBUG and above)
- `logs/info.log`: Contains INFO level and above messages
- `logs/error.log`: Contains only ERROR and CRITICAL messages

### Console Output

By default, the console shows only WARNING and above messages to keep the output clean. To enable debug output in the console:

1. Set the environment variable:
   ```bash
   export BOOKCHAT_DEBUG=true
   ```

2. Or add to your `.env` file:
   ```bash
   BOOKCHAT_DEBUG=true
   ```

### Log Levels

The logging system uses standard Python logging levels (from lowest to highest priority):
- DEBUG: Detailed information for debugging
- INFO: General operational messages
- WARNING: Warning messages for potential issues
- ERROR: Error messages for actual problems
- CRITICAL: Critical issues that need immediate attention

### Debugging Tips

1. Check the appropriate log file based on the severity of the issue:
   - For detailed debugging: `logs/debug.log`
   - For general operation info: `logs/info.log`
   - For errors and critical issues: `logs/error.log`

2. Enable console debug output temporarily using the `BOOKCHAT_DEBUG` environment variable

3. Log files include detailed information such as:
   - Timestamp
   - Log level
   - Source file and line number
   - Detailed message

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
