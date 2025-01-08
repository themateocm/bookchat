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
        self.keys_dir = Path(keys_dir) if keys_dir else Path.home() / '.bookchat' / 'keys'
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.private_key_path = self.keys_dir / 'private_key.pem'
        self.public_key_path = self.keys_dir / 'public_key.pem'
        
        # Load or generate keys
        self.private_key = None
        self.public_key = None
        self.load_or_generate_keys()

    def load_or_generate_keys(self):
        """Load existing keys or generate new ones if they don't exist."""
        if self.private_key_path.exists() and self.public_key_path.exists():
            self.load_keys()
        else:
            self.generate_keys()

    def generate_keys(self):
        """Generate new RSA key pair."""
        # Generate private key
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()

        # Save private key
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        self.private_key_path.write_bytes(private_pem)

        # Save public key
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.public_key_path.write_bytes(public_pem)

    def load_keys(self):
        """Load keys from files."""
        # Load private key
        private_pem = self.private_key_path.read_bytes()
        self.private_key = load_pem_private_key(private_pem, password=None)
        
        # Get public key from private key
        self.public_key = self.private_key.public_key()

    def sign_message(self, message_content):
        """Sign a message and return the signature."""
        if not self.private_key:
            return None
            
        signature = self.private_key.sign(
            message_content.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return b64encode(signature).decode()

    def verify_signature(self, message_content, signature, public_key_pem=None):
        """Verify a message signature using either local or provided public key."""
        try:
            if public_key_pem:
                public_key = serialization.load_pem_public_key(
                    public_key_pem.encode()
                )
            else:
                public_key = self.public_key

            public_key.verify(
                b64decode(signature),
                message_content.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except (InvalidSignature, ValueError):
            return False

    def get_public_key_pem(self):
        """Get public key in PEM format."""
        if not self.public_key:
            return None
        
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def export_public_key(self, export_path):
        """Export public key to a file."""
        if not self.public_key:
            return False
            
        public_pem = self.get_public_key_pem()
        Path(export_path).write_text(public_pem)
        return True
