-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    author TEXT DEFAULT 'anonymous',
    git_hash TEXT,  -- Store Git commit hash for version control
    parent_id INTEGER,  -- For message threading
    FOREIGN KEY (parent_id) REFERENCES messages(id)
);

-- Create index for faster querying
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_author ON messages(author);
CREATE INDEX IF NOT EXISTS idx_messages_parent ON messages(parent_id);

-- Create index for Git hash lookups
CREATE INDEX IF NOT EXISTS idx_messages_git_hash ON messages(git_hash);
