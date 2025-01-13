import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import logging

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

if __name__ == "__main__":
    main()
