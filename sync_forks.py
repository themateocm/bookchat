import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import logging
import hashlib
import json
from typing import Dict, Set
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('sync_forks.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

# Load the current repository from .env
load_dotenv()
current_repo = os.getenv("GITHUB_REPO")

# File paths
forks_file = "forks_list.txt"
base_dir = Path("cloned_repos")

# Ensure the base directory exists
base_dir.mkdir(exist_ok=True)

def run_command(command, cwd=None):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Error output: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running command: {' '.join(command)}\n{e}")

def get_unique_repo_name(repo_url):
    """Extract username and repo name from GitHub URL to create a unique directory name."""
    parts = repo_url.split('/')
    if len(parts) >= 2:
        username = parts[-2]
        repo_name = parts[-1]
        return f"{username}_{repo_name}"
    return repo_url.split("/")[-1]

def clone_or_update_repo(repo_url, subdir):
    """Clone or update a specific subdirectory from a repository."""
    repo_name = get_unique_repo_name(repo_url)
    local_path = base_dir / repo_name

    if not local_path.exists():
        logger.info(f"Cloning repository: {repo_url}")
        # First, do a full clone
        run_command(["git", "clone", "--filter=blob:none", "--no-checkout", repo_url, str(local_path)])
        run_command(["git", "config", "core.sparseCheckout", "true"], cwd=local_path)
        
        # Create sparse-checkout file with the exact path
        sparse_checkout_dir = local_path / ".git" / "info"
        sparse_checkout_dir.mkdir(parents=True, exist_ok=True)
        sparse_checkout_file = sparse_checkout_dir / "sparse-checkout"
        with open(sparse_checkout_file, "w") as f:
            f.write(f"{subdir}\n")  # Just the directory name
        
        # Checkout the sparse content
        run_command(["git", "checkout"], cwd=local_path)
    else:
        logger.debug(f"Updating existing repository: {repo_name}")
        run_command(["git", "pull"], cwd=local_path)
        run_command(["git", "checkout"], cwd=local_path)

def generate_message_hash(message_data: Dict) -> str:
    """Generate a deterministic hash from message content and metadata."""
    # Use relevant fields for deduplication
    hash_fields = {
        'content': message_data.get('content', ''),
        'user': message_data.get('user', ''),
        'timestamp': message_data.get('timestamp', ''),
        # Exclude fields that might differ between copies like file path
    }
    
    # Create deterministic string representation
    hash_str = json.dumps(hash_fields, sort_keys=True)
    return hashlib.sha256(hash_str.encode()).hexdigest()

def generate_message_filename(message_data: Dict) -> str:
    """Generate a consistent filename based on message timestamp and content.
    Format: YYYYMMDD_HHMMSS_<content_hash>.json
    """
    # Extract timestamp
    timestamp_str = message_data.get('timestamp', '')
    try:
        # Parse the timestamp and format it consistently
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        date_part = timestamp.strftime('%Y%m%d_%H%M%S')
    except (ValueError, TypeError):
        # If timestamp is invalid, use a fallback
        logger.warning(f"Invalid timestamp in message: {timestamp_str}")
        date_part = "00000000_000000"
    
    # Generate content hash
    hash_fields = {
        'content': message_data.get('content', ''),
        'user': message_data.get('user', ''),
        'timestamp': timestamp_str,
    }
    hash_str = json.dumps(hash_fields, sort_keys=True)
    content_hash = hashlib.sha256(hash_str.encode()).hexdigest()[:12]  # First 12 chars of hash
    
    return f"{date_part}_{content_hash}.json"

def copy_messages_to_main(base_dir):
    """Copy messages from cloned repos to main messages directory, avoiding duplicates."""
    main_messages_dir = Path("messages")
    main_messages_dir.mkdir(exist_ok=True)
    
    # Track message hashes to avoid duplicates
    seen_hashes: Set[str] = set()
    
    # First, load existing messages in main directory and rename them to new format
    existing_files = list(main_messages_dir.glob("*.json"))
    for existing_file in existing_files:
        try:
            with open(existing_file, 'r') as f:
                message_data = json.load(f)
            
            # Generate new filename
            new_filename = generate_message_filename(message_data)
            new_path = main_messages_dir / new_filename
            
            # Rename file if it doesn't match new format
            if existing_file.name != new_filename:
                logger.debug(f"Renaming {existing_file.name} to {new_filename}")
                if new_path.exists():
                    # If target exists, check if content is identical
                    with open(new_path, 'r') as f:
                        existing_content = json.load(f)
                    if generate_message_hash(existing_content) == generate_message_hash(message_data):
                        existing_file.unlink()  # Delete duplicate
                    else:
                        # Keep both by adding a numeric suffix
                        i = 1
                        while new_path.exists():
                            base, ext = new_filename.rsplit('.', 1)
                            new_path = main_messages_dir / f"{base}_{i}.{ext}"
                            i += 1
                        existing_file.rename(new_path)
                else:
                    existing_file.rename(new_path)
            
            # Add to seen hashes
            message_hash = generate_message_hash(message_data)
            seen_hashes.add(message_hash)
            
        except Exception as e:
            logger.error(f"Error processing existing message {existing_file}: {e}")
    
    # Track stats for logging
    total_messages = 0
    duplicate_count = 0
    copied_count = 0
    
    for repo_dir in base_dir.iterdir():
        if not repo_dir.is_dir():
            continue
            
        messages_dir = repo_dir / "messages"
        if not messages_dir.exists():
            continue
            
        logger.info(f"Processing messages from {repo_dir.name}")
        for message_file in messages_dir.glob("*.json"):
            total_messages += 1
            try:
                # Read message content
                with open(message_file, 'r') as f:
                    message_data = json.load(f)
                
                # Generate hash for deduplication
                message_hash = generate_message_hash(message_data)
                
                # Skip if we've seen this message before
                if message_hash in seen_hashes:
                    duplicate_count += 1
                    continue
                
                # Add source repo info to message metadata
                message_data['source_repo'] = repo_dir.name
                
                # Generate consistent filename
                new_filename = generate_message_filename(message_data)
                target_path = main_messages_dir / new_filename
                
                # Handle potential collisions
                if target_path.exists():
                    base, ext = new_filename.rsplit('.', 1)
                    i = 1
                    while target_path.exists():
                        target_path = main_messages_dir / f"{base}_{i}.{ext}"
                        i += 1
                
                # Save message with source repo info
                with open(target_path, 'w') as f:
                    json.dump(message_data, f, indent=2)
                
                seen_hashes.add(message_hash)
                copied_count += 1
                logger.debug(f"Copied unique message to {target_path.name}")
                
            except Exception as e:
                logger.error(f"Error processing {message_file}: {e}")
    
    logger.info(f"Message sync complete: {total_messages} total messages, "
               f"{duplicate_count} duplicates skipped, {copied_count} unique messages copied")

def main():
    if not Path(forks_file).exists():
        logger.error(f"Error: {forks_file} not found.")
        return

    with open(forks_file, "r") as f:
        repos = [line.strip() for line in f if line.strip()]

    if current_repo:
        repos = [repo for repo in repos if current_repo not in repo]

    for repo in repos:
        clone_or_update_repo(repo, "messages")
        
    # Copy messages from all forks to main messages directory
    copy_messages_to_main(base_dir)

if __name__ == "__main__":
    main()
