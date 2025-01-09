# BookChat - Git-Backed Messaging Application

A lightweight, Git-backed web-based messaging application that allows users to communicate through a simple interface while maintaining message history in a Git repository.

## Features

- Simple and intuitive web interface
- Flexible storage backend (Git or SQLite)
- Git integration for message history
- Real-time message updates
- Basic user authentication
- Markdown support for messages
- Serverless-friendly when using Git storage

## Tech Stack

- Backend: Python (No frameworks)
- Storage: Git-based JSON files or SQLite database
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
│   ├── git_storage.py
│   └── sqlite_storage.py
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
   # Choose storage backend: 'git' or 'sqlite'
   BOOKCHAT_STORAGE=git
   
   # For Git storage
   REPO_PATH=/path/to/your/repo
   
   # For SQLite storage
   DB_PATH=/path/to/database.db
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
- Use either Git or SQLite storage
- Deploy on any Python-compatible hosting platform
- Suitable for larger deployments with more control

### 3. Serverless Platforms
- Use Git storage backend
- Deploy on platforms like Vercel, Netlify, or Cloudflare Pages
- Great for scalable, maintenance-free deployments

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
