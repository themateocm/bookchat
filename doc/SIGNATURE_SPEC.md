# BookChat Message Signing Specification

## Overview
BookChat implements a robust public key-based message signing system to verify message authenticity. Each user's messages are signed with their private key and can be verified using their public key.

## Key Management

### Key Generation and Storage
- RSA key pairs (2048-bit) are generated using OpenSSL
- Private key stored locally as `keys/local.pem`
- Public key stored in `public_keys/<username>.pub`
- Each user has a unique key pair
- Key format: PEM
- Key size: 2048 bits

### Key Manager Implementation
```python
class KeyManager:
    def __init__(self, keys_dir)  # Initialize key manager and generate keys if needed
    def sign_message(self, message)  # Sign message with private key
    def verify_signature(self, message, signature_hex, public_key_pem)  # Verify message signature
    def export_public_key(self, path)  # Export public key to specified path
```

## Message Signing Process

### Message Format
```
Date: <ISO format date>
Author: <username>
Parent-Message: <parent_id>  # Optional
Type: <message_type>
Signature: <hex_encoded_signature>

<message_content>
```

### Signing Steps
1. Message content is encoded to UTF-8 bytes
2. SHA-256 digest is created
3. Digest is signed using the private key
4. Signature is hex-encoded and stored in message header

### Verification Steps
1. Message content is extracted (everything after blank line)
2. Content is encoded to UTF-8 bytes
3. Signature is hex-decoded to bytes
4. OpenSSL verifies the signature using author's public key

### OpenSSL Commands

#### Generate Key Pair
```bash
openssl genrsa -out local.pem 2048
openssl rsa -pubout -in local.pem -out local.pub
```

#### Sign Message
```bash
openssl dgst -sha256 -sign local.pem -out signature.bin message.txt
```

#### Verify Signature
```bash
openssl dgst -sha256 -verify public.pub -signature signature.bin message.txt
```

## Username Management Security

### Username Change Process
1. User signs a special message type indicating username change
2. Message includes old and new username as JSON
3. Server verifies signature with old username's public key
4. If valid, moves public key to new username file
5. All future messages must use new username

### Username Verification
1. Server checks message history for username changes
2. Verifies public key exists for username
3. Returns verified username or 'anonymous'

## Implementation Example

Here's a minimal Python example of the signing mechanism:

```python
import subprocess
from pathlib import Path

def sign_message(message: str, private_key_path: str) -> str:
    """Sign a message using RSA private key"""
    result = subprocess.run(
        ['openssl', 'dgst', '-sha256', '-sign', private_key_path],
        input=message.encode(),
        capture_output=True,
        check=True
    )
    return result.stdout.hex()

def verify_signature(
    message: str,
    signature_hex: str,
    public_key_pem: str,
    temp_dir: Path
) -> bool:
    """Verify a message signature using RSA public key"""
    sig_path = temp_dir / 'temp.sig'
    pub_path = temp_dir / 'temp.pub'
    
    try:
        # Write signature and public key to temp files
        sig_path.write_bytes(bytes.fromhex(signature_hex))
        pub_path.write_text(public_key_pem)
        
        # Verify signature
        result = subprocess.run(
            ['openssl', 'dgst', '-sha256', '-verify', str(pub_path),
             '-signature', str(sig_path)],
            input=message.encode(),
            capture_output=True
        )
        return result.returncode == 0
    finally:
        # Clean up temp files
        if sig_path.exists():
            sig_path.unlink()
        if pub_path.exists():
            pub_path.unlink()
```

## Security Considerations

### Current Implementation
- ✅ Message signing with RSA keys
- ✅ Message verification
- ✅ Username-key binding
- ✅ User key management

### Future Improvements
1. **Key Management Enhancements**
   - Key rotation support
   - Key revocation support
   - Multiple device support

2. **Security Features**
   - Add timestamp verification
   - Implement signature expiration
   - Add message encryption
   - Add forward secrecy

3. **Multiple Devices Support**
   - Implement device registration protocol
   - Allow multiple public keys per username
   - Add device ID to message headers
   - Store device-specific public keys
   - Implement key synchronization

4. **Message Threading Security**
   - Thread signing (sign entire conversation)
   - Thread verification
   - Thread encryption
   - Forward secrecy per thread

*Last updated: 2025-01-13*
