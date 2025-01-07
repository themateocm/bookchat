# BookChat - Git-Backed Messaging Application

A lightweight, Git-backed web-based messaging application that allows users to communicate through a simple interface while maintaining message history in a Git repository.

## Features

- Simple and intuitive web interface
- Message persistence using SQLite database
- Git integration for message history
- Real-time message updates
- Basic user authentication
- Markdown support for messages

## Tech Stack

- Backend: Python (No frameworks)
- Database: SQLite
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
├── database/
│   └── schema.sql
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

4. Set up your GitHub OAuth application and update the `.env` file with your credentials:
   ```
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   SECRET_KEY=your_secret_key
   ```

5. Initialize the database:
   ```bash
   python server.py init-db
   ```

6. Run the application:
   ```bash
   python server.py
   ```

7. Open your browser and navigate to `http://localhost:8000`

## Development

This project is being developed incrementally with a focus on simplicity and maintainability. Each component is built without relying on heavy frameworks to maintain clarity and ease of understanding.

## License

MIT License - Feel free to use this project for learning or building your own messaging application.
