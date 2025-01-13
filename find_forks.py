"""
GitHub Repository Fork Finder
----------------------------
This script identifies and lists all forks of a specified GitHub repository. It traverses
the fork tree to find both direct forks and forks of forks, creating a comprehensive
list of all derivative repositories.

Features:
- Authenticates with GitHub using a personal access token
- Handles both direct forks and nested forks
- Outputs results to a text file
- Includes error handling for API requests
- Supports both public and private repositories (with appropriate permissions)

Requirements:
- Python 3.x
- GitHub Personal Access Token with repo scope
- Environment variables in .env file:
  - GITHUB_TOKEN: Your GitHub personal access token
  - GITHUB_REPO: Target repository URL to find forks for

Output:
- Creates 'forks_list.txt' containing URLs of all discovered forks

Last Updated: 2025-01-13
"""

import requests
import sys
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Load GitHub token
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is missing in the .env file!")

GITHUB_REPO = os.getenv("GITHUB_REPO")  # Load repository from .env file
if not GITHUB_REPO:
    raise ValueError("GITHUB_REPO is missing in the .env file!")

OUTPUT_FILE = "forks_list.txt"

def get_repo_details(repo_url):
    """Extract owner and repo name from the GitHub URL."""
    parts = repo_url.rstrip('/').split('/')
    if len(parts) < 2:
        raise ValueError("Invalid GitHub URL")
    return parts[-2], parts[-1]


def make_request(url):
    """Make a GET request to the GitHub API."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        sys.exit(1)
    return response.json()


def find_root_repo(owner, repo):
    """Find the root repository if the given repo is a fork."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data = make_request(url)
    if data.get("fork"):
        parent = data.get("parent", {})
        return parent.get("owner", {}).get("login"), parent.get("name")
    return owner, repo


def get_all_forks(owner, repo):
    """Get all forks of a repository."""
    forks = []
    url = f"https://api.github.com/repos/{owner}/{repo}/forks"
    while url:
        data = make_request(url)
        forks.extend([f["html_url"] for f in data])
        url = requests.utils.urlparse(data.links.get("next", {}).get("url", "")).geturl()
    return forks


def traverse_fork_tree(root_owner, root_repo):
    """Traverse the fork tree and collect all forks."""
    visited = set()
    queue = [(root_owner, root_repo)]
    all_forks = []

    while queue:
        owner, repo = queue.pop(0)
        if (owner, repo) in visited:
            continue
        visited.add((owner, repo))
        print(f"Processing: {owner}/{repo}")
        forks = get_all_forks(owner, repo)
        all_forks.extend(forks)
        for fork_url in forks:
            fork_owner, fork_repo = get_repo_details(fork_url)
            queue.append((fork_owner, fork_repo))

    return all_forks


def main():
    input_url = input("Enter the GitHub repository URL: ").strip()
    root_owner, root_repo = get_repo_details(input_url)

    # Find the root repository
    root_owner, root_repo = find_root_repo(root_owner, root_repo)
    print(f"Root repository: {root_owner}/{root_repo}")

    # Traverse the fork tree
    all_forks = traverse_fork_tree(root_owner, root_repo)

    # Write to output file
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(all_forks))

    print(f"Forks written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
