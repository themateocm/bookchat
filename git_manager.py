#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime
from pathlib import Path
from github import Github
import json
import re
import shutil
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class KeyManager:
    def __init__(self, private_keys_dir, public_keys_dir):
        self.private_keys_dir = Path(private_keys_dir)
        self.public_keys_dir = Path(public_keys_dir)
        self.private_keys_dir.mkdir(parents=True, exist_ok=True)
        self.public_keys_dir.mkdir(parents=True, exist_ok=True)
        self.private_key_path = self.private_keys_dir / 'local.pem'
        self.public_key_path = self.public_keys_dir / 'local.pub'
        
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
        sig_path = self.private_keys_dir / 'temp.sig'
        try:
            # Convert hex signature back to bytes and write to file
            signature_bytes = bytes.fromhex(signature_hex)
            sig_path.write_bytes(signature_bytes)

            #todo the pub key should be stored in a way that
            # it can be used again next time, and can also be
            # downloaded by the web browser

            # Write public key to temp file
            pub_path = self.private_keys_dir / 'temp.pub'
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

    def generate_keypair(self, username):
        """Generate key pair for the user"""
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()

        # Save private key
        private_key_path = self.private_keys_dir / f'{username}.pem'
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        private_key_path.write_bytes(private_pem)

        # Save public key
        public_key_path = self.public_keys_dir / f'{username}.pub'
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        public_key_path.write_bytes(public_pem)

    def get_private_key_path(self, username):
        # Get private key path for the user
        return self.private_keys_dir / f'{username}.pem'

    def get_public_key(self, username):
        # Get public key for the user
        public_key_path = self.public_keys_dir / f'{username}.pub'
        if public_key_path.exists():
            return public_key_path.read_text()
        else:
            return None

class GitManager:
    def __init__(self, repo_path):
        """Initialize GitManager with repository path and GitHub credentials."""
        self.repo_path = Path(repo_path)
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.repo_name = os.environ.get('GITHUB_REPO')
        self.should_sync_to_github = os.environ.get('SYNC_TO_GITHUB', '').lower() == 'true'
        
        # Initialize key manager with both private and public key directories
        private_keys_dir = os.environ.get('KEYS_DIR', str(self.repo_path / 'keys'))
        public_keys_dir = os.environ.get('PUBLIC_KEYS_DIR', str(self.repo_path / 'identity/public_keys'))
        self.key_manager = KeyManager(private_keys_dir, public_keys_dir)
        
        # Make GitHub optional
        self.use_github = bool(self.github_token and self.repo_name and self.should_sync_to_github)
        if self.use_github:
            print("GitHub synchronization enabled")
            # Initialize GitHub API client
            self.g = Github(self.github_token)
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
        public_keys_dir = self.repo_path / 'identity/public_keys'
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
        remote_url = f'https://{self.github_token}@github.com/{self.repo_name}.git'
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
            # Ensure filepath is a Path object
            filepath = Path(filepath) if not isinstance(filepath, Path) else filepath
            
            # Check if the file exists before trying to sync
            if not filepath.exists():
                print(f"Warning: File {filepath} does not exist, skipping GitHub sync")
                return
            
            # Stage the file
            relative_path = filepath.relative_to(self.repo_path)
            subprocess.run(['git', 'add', str(relative_path)], cwd=str(self.repo_path), check=True)
            
            # Check if there are any changes to commit
            status = subprocess.run(
                ['git', 'status', '--porcelain', str(relative_path)],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True
            )
            
            if not status.stdout.strip():
                print(f"No changes to commit for {relative_path}")
                return
            
            # Commit the change
            commit_message = f'Update user key for {author}'
            subprocess.run(
                ['git', 'commit', '--no-verify', '-m', commit_message],
                cwd=str(self.repo_path),
                check=True,
                env={**os.environ, 'GIT_AUTHOR_NAME': author, 'GIT_AUTHOR_EMAIL': f'{author}@bookchat.local'}
            )
            
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
        """Format a message with metadata footers."""
        footers = [
            f"Author: {author}",
            f"Date: {date_str}",
            f"Public-Key: identity/public_keys/{author}.pub"
        ]
        
        if parent_id:
            footers.append(f"Parent-Message: {parent_id}")
        
        if signature:
            footers.append(f"Signature: {signature}")
            
        if message_type:
            footers.append(f"Type: {message_type}")
        
        # Combine message and footers with standard email separator
        return f"{message_content.rstrip()}\n\n-- \n{chr(10).join(footers)}"

    def parse_message(self, content):
        """Parse a message into metadata and content."""
        # Split on standard email signature separator
        parts = content.split('\n-- \n', 1)
        if len(parts) != 2:
            return {}, parts[0].strip()
            
        message = parts[0].strip()
        metadata = {}
        
        # Parse metadata footers
        for line in parts[1].strip().split('\n'):
            if ': ' in line:
                key, value = line.split(': ', 1)
                metadata[key] = value
                
        return metadata, message

    def read_message(self, filename):
        """Read a message from a file."""
        filepath = self.messages_dir / filename
        if not filepath.exists():
            return None
            
        content = filepath.read_text()
        
        # First try to parse as JSON for backward compatibility
        try:
            json_data = json.loads(content)
            if isinstance(json_data, dict):
                # Convert old JSON format to new format
                return {
                    'id': filename,
                    'content': json_data.get('content', ''),
                    'author': json_data.get('author', 'anonymous'),
                    'createdAt': json_data.get('timestamp'),  
                    'parent_id': json_data.get('parent_id'),
                    'signed': 'signature' in json_data,
                    'verified': str(json_data.get('verified', False)).lower(),
                    'type': json_data.get('type', 'message')
                }
        except json.JSONDecodeError:
            # Not JSON, parse as plaintext with footers
            metadata, message = self.parse_message(content)
            
            # Try to parse date in multiple formats
            date = metadata.get('Date')
            if date:
                try:
                    # Try to parse as ISO format first
                    parsed_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    # Format as RFC 3339 with proper timezone offset
                    date_str = parsed_date.astimezone().strftime('%Y-%m-%dT%H:%M:%S%z')
                    date = date_str[:-2] + ':' + date_str[-2:]  # Insert colon in timezone offset
                except ValueError:
                    try:
                        # Try to parse from filename (YYYYMMDD_HHMMSS)
                        parts = filename.split('_')
                        if len(parts) >= 2:
                            date = f"{parts[0][:4]}-{parts[0][4:6]}-{parts[0][6:]}T{parts[1][:2]}:{parts[1][2:4]}:{parts[1][4:]}Z"
                    except:
                        pass
            
            # Verify signature if present
            verified = self.verify_message(message, metadata)
            metadata['verified'] = str(verified if verified is not None else False).lower()
            
            return {
                'id': filename,
                'content': message,
                'author': metadata.get('Author', 'anonymous'),
                'createdAt': date,  
                'parent_id': metadata.get('Parent-Message'),
                'signed': 'Signature' in metadata,
                'verified': metadata['verified'],
                'type': metadata.get('Type', 'message'),
                'public_key': metadata.get('Public-Key')
            }

    def verify_message(self, content, metadata):
        """Verify message signature if present."""
        signature = metadata.get('Signature')
        if not signature:
            return None  # Message is not signed
            
        # Try to find author's public key
        author = metadata.get('Author', 'anonymous')
        
        try:
            public_key = self.key_manager.get_public_key(author)
            if not public_key:
                return False  # Can't verify - no public key
                
            return self.key_manager.verify_signature(content, signature, public_key)
        except ValueError:
            return False  # Invalid signature format

    def handle_username_change(self, old_username, new_username, message_id=None):
        """Handle username change request after verification"""
        try:
            # Validate new username format
            USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
            if not USERNAME_REGEX.match(new_username):
                return False, "Username must be 3-20 characters long and contain only letters, numbers, and underscores"
            
            try:
                # Ensure the public_keys directory exists
                public_keys_dir = self.repo_path / 'identity/public_keys'
                public_keys_dir.mkdir(exist_ok=True)
                
                # Generate new keypair for the user
                self.key_manager.generate_keypair(new_username)
                
                # If there was an old username, clean up its keys
                old_key_path = self.repo_path / 'identity/public_keys' / f'{old_username}.pub'
                if old_key_path.exists():
                    old_key_path.unlink()
                    old_private_key = self.key_manager.get_private_key_path(old_username)
                    if old_private_key.exists():
                        old_private_key.unlink()
                
                # Sync to GitHub if enabled
                if self.use_github:
                    new_key_path = self.repo_path / 'identity/public_keys' / f'{new_username}.pub'
                    self.sync_changes_to_github(new_key_path, new_username)
                
                return True, "Username changed successfully"
            except OSError as e:
                # If operation fails, return error
                return False, f"Failed to update username: {str(e)}"
                
        except Exception as e:
            return False, f"Username change failed: {str(e)}"

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

    def add_and_commit_file(self, filepath: str, commit_msg: str, author: str = "BookChat Bot"):
        """Add and commit a specific file.
        
        Args:
            filepath: Path to the file to commit
            commit_msg: Commit message
            author: Author of the commit
        """
        try:
            # Check if file has changes to commit
            status = subprocess.run(
                ['git', 'status', '--porcelain', filepath],
                cwd=str(self.repo_path),
                check=True,
                capture_output=True,
                text=True
            )
            
            # If no changes, return early
            if not status.stdout.strip():
                return True
            
            # Add the specific file
            subprocess.run(
                ['git', 'add', filepath],
                cwd=str(self.repo_path),
                check=True,
                capture_output=True,
                text=True
            )
            
            # Commit the file
            subprocess.run(
                ['git', 'commit', '--no-verify', filepath, '-m', commit_msg],
                cwd=str(self.repo_path),
                check=True,
                capture_output=True,
                text=True,
                env={**os.environ, 'GIT_AUTHOR_NAME': author, 'GIT_AUTHOR_EMAIL': f'{author}@bookchat.local'}
            )
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error in git operations: {e.stderr}")
            return False

    def push(self):
        """Push changes to remote repository."""
        try:
            # Check if there are commits to push
            status = subprocess.run(
                ['git', 'status', '-sb'],
                cwd=str(self.repo_path),
                check=True,
                capture_output=True,
                text=True
            )
            
            # If nothing to push, return early
            if 'ahead' not in status.stdout:
                return True
                
            subprocess.run(
                ['git', 'push'],
                cwd=str(self.repo_path),
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error pushing to remote: {e.stderr}")
            return False

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
