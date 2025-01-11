#!/usr/bin/env python3

import os
import json
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.exceptions import InvalidSignature
from base64 import b64encode, b64decode

class KeyManager:
    def __init__(self, keys_dir=None):
        """Initialize KeyManager with directory for key storage."""
        self.keys_dir = Path(keys_dir) if keys_dir else Path('public_keys')
        self.keys_dir.mkdir(parents=True, exist_ok=True)

    def has_key_pair(self, username):
        """Check if a user has a key pair."""
        key_file = self.keys_dir / f"{username}.pub"
        return key_file.exists()

    def get_public_key(self, username):
        """Get a user's public key."""
        key_file = self.keys_dir / f"{username}.pub"
        if key_file.exists():
            return key_file.read_text().strip()
        return None

    def sign_message(self, message_content, username):
        """Sign a message for a user."""
        key_file = self.keys_dir / f"{username}.pub"
        if not key_file.exists():
            return None
        return "signed"  # Simplified for now, we'll implement real signing later

    def verify_signature(self, message_content, signature, username):
        """Verify a message signature."""
        key_file = self.keys_dir / f"{username}.pub"
        if not key_file.exists():
            return False
        return True  # Simplified for now, we'll implement real verification later
