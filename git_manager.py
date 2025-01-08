#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime
from pathlib import Path
from github import Github
import json

class KeyManager:
    def __init__(self, keys_dir):
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.private_key_path = self.keys_dir / 'local.pem'
        self.public_key_path = self.keys_dir / 'local.pub'
        
        # Generate key pair if it doesn't exist
        if not self.private_key_path.exists():
            subprocess.run(['openssl', 'genrsa', '-out', str(self.private_key_path), '2048'], check=True)
            subprocess.run(['openssl', 'rsa', '-pubout', '-in', str(self.private_key_path), '-out', str(self.public_key_path)], check=True)
    
    def sign_message(self, message):
        # Sign message with private key
        signature = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', str(self.private_key_path)], input=message.encode(), capture_output=True, check=True).stdout
        return signature.hex()
    
    def verify_signature(self, message, signature_hex, public_key_pem):
        # Write signature to temp file
        sig_path = self.keys_dir / 'temp.sig'
        try:
            # Convert hex signature back to bytes and write to file
            signature_bytes = bytes.fromhex(signature_hex)
            sig_path.write_bytes(signature_bytes)
            
            # Write public key to temp file
            pub_path = self.keys_dir / 'temp.pub'
            pub_path.write_text(public_key_pem)
            
            # Verify signature
            result = subprocess.run(
                ['openssl', 'dgst', '-sha256', '-verify', str(pub_path), '-signature', str(sig_path)],
                input=message.encode(),
                capture_output=True
            )
            return result.returncode == 0
        except (ValueError, subprocess.CalledProcessError) as e:
            print(f"Signature verification failed: {e}")
            return False
        finally:
            # Clean up temp files
            if sig_path.exists():
                sig_path.unlink()
            if pub_path.exists():
                pub_path.unlink()
    
    def export_public_key(self, filepath):
        # Export public key to file
        subprocess.run(['cp', str(self.public_key_path), str(filepath)], check=True)

class GitManager:
    def __init__(self, repo_path):
        """Initialize GitManager with repository path and GitHub credentials."""
        self.repo_path = Path(repo_path)
        self.token = os.environ.get('GITHUB_TOKEN')
        self.repo_name = os.environ.get('GITHUB_REPO')
        self.should_sync_to_github = os.environ.get('SYNC_TO_GITHUB', '').lower() == 'true'
        
        # Initialize key manager
        keys_dir = os.environ.get('KEYS_DIR', str(self.repo_path / 'keys'))
        self.key_manager = KeyManager(keys_dir)
        
        # Make GitHub optional
        self.use_github = bool(self.token and self.repo_name and self.should_sync_to_github)
        if self.use_github:
            print("GitHub synchronization enabled")
            # Initialize GitHub API client
            self.g = Github(self.token)
            self.repo = self.g.get_repo(self.repo_name)
            
            # Initialize git repository if needed
            if not (self.repo_path / '.git').exists():
                self.init_git_repo()
        else:
            print("GitHub synchronization disabled")
        
        # Set up messages directory path
        self.messages_dir = self.repo_path / 'messages'
        self.messages_dir.mkdir(parents=True, exist_ok=True)
        
        # Export public key for anonymous users
        public_keys_dir = self.repo_path / 'public_keys'
        public_keys_dir.mkdir(parents=True, exist_ok=True)
        self.key_manager.export_public_key(public_keys_dir / 'anonymous.pub')
        
        # Sync public key if GitHub is enabled
        if self.use_github:
            self.sync_changes_to_github(public_keys_dir / 'anonymous.pub', "System")

    def init_git_repo(self):
        """Initialize git repository and set up remote."""
        if not self.use_github:
            return

        # Initialize git repository
        subprocess.run(['git', 'init'], cwd=str(self.repo_path), check=True)
        
        # Configure git
        subprocess.run(['git', 'config', 'user.name', 'BookChat Bot'], cwd=str(self.repo_path), check=True)
        subprocess.run(['git', 'config', 'user.email', 'bot@bookchat.local'], cwd=str(self.repo_path), check=True)
        
        # Add GitHub remote
        remote_url = f'https://{self.token}@github.com/{self.repo_name}.git'
        subprocess.run(['git', 'remote', 'add', 'origin', remote_url], cwd=str(self.repo_path), check=True)
        
        # Pull existing content
        try:
            subprocess.run(['git', 'pull', 'origin', 'main'], cwd=str(self.repo_path), check=True)
        except subprocess.CalledProcessError:
            # If pull fails, create and push initial commit
            subprocess.run(['git', 'checkout', '-b', 'main'], cwd=str(self.repo_path), check=True)

    def sync_changes_to_github(self, filepath, author="BookChat Bot"):
        """Sync changes to GitHub."""
        if not self.use_github:
            return

        try:
            # Stage the file
            relative_path = filepath.relative_to(self.repo_path)
            subprocess.run(['git', 'add', str(relative_path)], cwd=str(self.repo_path), check=True)
            
            # Commit the change
            commit_message = f'Add message from {author}'
            subprocess.run(['git', 'commit', '-m', commit_message], cwd=str(self.repo_path), check=True)
            
            # Push to GitHub
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=str(self.repo_path), check=True)
            print(f"Successfully synced {relative_path} to GitHub")
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to sync to GitHub: {e}")
            # Continue without GitHub sync - don't raise the error

    def ensure_repo_exists(self):
        """Ensure the repository exists locally, clone if it doesn't."""
        # Create messages directory if it doesn't exist
        self.messages_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep to ensure directory is tracked
        gitkeep_path = self.messages_dir / '.gitkeep'
        if not gitkeep_path.exists():
            gitkeep_path.touch()

    def format_message(self, message_content, author, date_str, parent_id=None, signature=None, message_type=None):
        """Format a message with metadata headers."""
        header = []
        header.append(f"Date: {date_str}")
        header.append(f"Author: {author}")
        if parent_id:
            header.append(f"Parent-Message: {parent_id}")
        if signature:
            header.append(f"Signature: {signature}")
        if message_type:
            header.append(f"Type: {message_type}")
        
        # Join headers and add blank line before content
        return "\n".join(header) + "\n\n" + message_content

    def parse_message(self, content):
        """Parse a message file content into metadata and message."""
        lines = content.split("\n")
        metadata = {}
        message_start = 0
        
        # Parse headers
        for i, line in enumerate(lines):
            if not line.strip():  # Empty line marks end of headers
                message_start = i + 1
                break
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
        
        # Get message content
        message = "\n".join(lines[message_start:]).strip()
        
        return metadata, message

    def verify_message(self, content, metadata):
        """Verify message signature if present."""
        signature = metadata.get('Signature')
        if not signature:
            return None  # Message is not signed
            
        # Try to find author's public key
        author = metadata.get('Author', 'anonymous')
        public_key_path = self.repo_path / 'public_keys' / f'{author}.pub'
        
        if not public_key_path.exists():
            return False  # Can't verify - no public key
            
        try:
            public_key_pem = public_key_path.read_text()
            return self.key_manager.verify_signature(content, signature, public_key_pem)
        except ValueError:
            return False  # Invalid signature format

    def handle_username_change(self, old_username, new_username, message_id):
        """Handle username change request after verification"""
        try:
            # Move the public key file
            old_key_path = self.repo_path / 'public_keys' / f'{old_username}.pub'
            new_key_path = self.repo_path / 'public_keys' / f'{new_username}.pub'
            
            if not old_key_path.exists():
                return False, "Old username's public key not found"
            
            # If it's the same username, consider it a success
            if old_username == new_username:
                return True, "Username unchanged"
                
            if new_key_path.exists():
                return False, "New username already exists"
            
            # Read the message to verify it's a valid username change request
            message = self.read_message(message_id)
            if not message:
                return False, "Message not found"
                
            if message['type'] != 'username_change' or not message['verified']:
                return False, "Invalid or unverified username change request"
                
            if message['author'] != old_username:
                return False, "Username mismatch"
                
            # Move the public key file
            old_key_path.rename(new_key_path)
            
            return True, "Username changed successfully"
        except Exception as e:
            return False, str(e)

    def save_message(self, message_content, author="anonymous", parent_id=None, date_str=None, sign=True, message_type=None):
        """Save a message to a file and optionally sync to GitHub."""
        # Ensure messages directory exists
        self.ensure_repo_exists()
        
        # Use current time if no date provided
        if date_str is None:
            date_str = datetime.now().isoformat()
        
        # Sign message if requested
        signature = None
        if sign:
            signature = self.key_manager.sign_message(message_content)
        
        # Create a timestamped filename
        timestamp = datetime.fromisoformat(date_str).strftime('%Y%m%d_%H%M%S')
        filename = f'{timestamp}_{author}.txt'
        filepath = self.messages_dir / filename
        
        # Format message with metadata
        formatted_message = self.format_message(
            message_content, 
            author, 
            date_str, 
            parent_id=parent_id,
            signature=signature,
            message_type=message_type
        )
        
        # Write message to file
        filepath.write_text(formatted_message)
        
        # Handle username change if this is a username change message
        if message_type == 'username_change':
            try:
                new_username = json.loads(message_content)['new_username']
                success, msg = self.handle_username_change(author, new_username, filename)
                if not success:
                    # If username change failed, add error message
                    error_msg = self.save_message(
                        f"Username change failed: {msg}",
                        "system",
                        parent_id=filename,
                        message_type="error"
                    )
            except (json.JSONDecodeError, KeyError) as e:
                # If message format is invalid, add error message
                error_msg = self.save_message(
                    f"Invalid username change message format: {e}",
                    "system",
                    parent_id=filename,
                    message_type="error"
                )
        
        # Sync to GitHub if enabled
        if self.use_github:
            self.sync_changes_to_github(filepath, author)
            
        return filename

    def read_message(self, filename):
        """Read a message from a file."""
        filepath = self.messages_dir / filename
        if not filepath.exists():
            return None
            
        content = filepath.read_text()
        metadata, message = self.parse_message(content)
        
        # Verify signature if present
        verified = self.verify_message(message, metadata)
        metadata['verified'] = str(verified if verified is not None else False).lower()
        
        return {
            'id': filename,
            'content': message,
            'author': metadata.get('Author', 'anonymous'),
            'date': metadata.get('Date'),
            'parent_id': metadata.get('Parent-Message'),
            'signed': 'Signature' in metadata,
            'verified': metadata['verified'],
            'type': metadata.get('Type', 'message')
        }

def main():
    """Main function for testing"""
    try:
        # Get repository path from environment
        repo_path = os.getenv('REPO_PATH')
        if not repo_path:
            raise ValueError("REPO_PATH environment variable is required")

        # Initialize GitManager
        manager = GitManager(repo_path)
        
        # Save a test message
        filename = manager.save_message("Test message", "test_user")
        
        # Print results
        print("Message saved successfully!")
        print(f"Filename: {filename}")
        
    except Exception as e:
        print(f"Error: {e}")
