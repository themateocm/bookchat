# BookChat Deployment Guide

This guide covers how to deploy and configure BookChat in various environments.

## Prerequisites

- Python 3.7 or higher
- Git
- OpenSSL
- A GitHub account (optional, for message synchronization)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bookchat.git
   cd bookchat
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy the environment template:
   ```bash
   cp .env.template .env
   ```

2. Configure the following environment variables in `.env`:

### Required Settings
- `PORT`: Server port (default: 8000)

### GitHub Integration (Optional)
- `SYNC_TO_GITHUB`: Enable GitHub synchronization (true/false)
- `GITHUB_TOKEN`: Your GitHub personal access token
- `GITHUB_REPO`: Repository name (format: username/repository)

### Security Settings
- `KEYS_DIR`: Directory for storing private keys (default: repo/keys)
- `SIGN_MESSAGES`: Enable message signing (true/false)
- `MESSAGE_VERIFICATION`: Enable message verification (true/false)

### Logging Configuration
- `BOOKCHAT_DEBUG`: Enable debug logging (set any value to enable)

### Archive Settings
- `ARCHIVE_INTERVAL_SECONDS`: Interval between archive checks (default: 3600)
- `ARCHIVE_DAYS_THRESHOLD`: Days before messages are archived (default: 30)
- `ARCHIVE_MAX_SIZE_MB`: Maximum archive size in MB (default: 100)

## Directory Structure

```
bookchat/
├── keys/                 # Private keys storage
├── identity/
│   └── public_keys/     # Public keys storage
├── messages/            # Active messages
├── archive/            # Archived messages
├── logs/               # Application logs
│   ├── debug.log
│   ├── info.log
│   └── error.log
└── static/             # Static web assets
```

## Running the Server

1. Start the server:
   ```bash
   python server.py
   ```

2. Access the application:
   - Open a web browser and navigate to `http://localhost:8000`
   - The server will automatically find an available port if 8000 is in use

## Logging

BookChat uses a hierarchical logging system:

1. Console Output:
   - Default: WARNING and above
   - Debug mode: All levels when BOOKCHAT_DEBUG is set

2. Log Files:
   - `debug.log`: All messages (DEBUG and above)
   - `info.log`: INFO and above
   - `error.log`: ERROR and above

## Security Considerations

1. Key Management:
   - Private keys are stored in `KEYS_DIR`
   - Public keys are stored in `identity/public_keys`
   - Keys are generated automatically if not present

2. Message Signing:
   - Enable `SIGN_MESSAGES` for message authentication
   - Enable `MESSAGE_VERIFICATION` for signature verification

3. GitHub Integration:
   - Use a dedicated GitHub account/token
   - Set appropriate repository permissions
   - Consider private repository for sensitive messages

## Troubleshooting

1. Port Conflicts:
   - The server automatically finds an available port
   - Check logs for the actual port being used

2. GitHub Sync Issues:
   - Verify GitHub token permissions
   - Check network connectivity
   - Review error logs for detailed messages

3. Key Management Issues:
   - Ensure proper directory permissions
   - Check OpenSSL installation
   - Verify key file ownership

## Maintenance

1. Log Rotation:
   - Logs are automatically rotated based on size
   - Archive old logs periodically

2. Message Archiving:
   - Messages are automatically archived based on age and size
   - Configure archive settings in `.env`

3. Backup Strategy:
   - Regular backup of `keys/` directory
   - Backup of `messages/` directory
   - GitHub serves as remote backup when enabled

*Last updated: 2025-01-13*
