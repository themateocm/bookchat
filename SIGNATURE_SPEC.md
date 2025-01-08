# BookChat Message Signing Specification

## Overview
BookChat implements a public key-based message signing system to verify message authenticity. Each user's messages are signed with their private key and can be verified using their public key.

## Current Implementation Status
- ✅ Message signing with RSA keys
- ✅ Message verification
- ❌ Username management (currently hardcoded to "anonymous")
- ❌ User key management (currently one key pair per server)
- ❌ Username-key binding

## Key Management

### Key Generation
- RSA key pairs (2048-bit) are generated using OpenSSL
- Private key stored in `keys/local.pem`
- Public key stored in `keys/local.pub`
- Currently, one key pair is generated per server instance

### Key Storage
- Private keys: `keys/local.pem`
- Public keys: `public_keys/<username>.pub`
- All anonymous users currently share the same key pair

## Message Format

### File Naming
Messages are stored in files with the format:
```
YYYYMMDD_HHMMSS_username.txt
```

### Message Structure
```
Date: <ISO format date>
Author: <username>
Parent-Message: <parent_id>  # Optional
Signature: <hex_encoded_signature>

<message_content>
```

### Signing Process
1. Message content is encoded to UTF-8 bytes
2. SHA-256 digest is created
3. Digest is signed using the private key
4. Signature is hex-encoded and stored in message header

### Verification Process
1. Message content is extracted (everything after blank line)
2. Content is encoded to UTF-8 bytes
3. Signature is hex-decoded to bytes
4. OpenSSL verifies the signature using author's public key

## OpenSSL Commands Used

### Generate Key Pair
```bash
openssl genrsa -out local.pem 2048
openssl rsa -pubout -in local.pem -out local.pub
```

### Sign Message
```bash
openssl dgst -sha256 -sign local.pem -out signature.bin message.txt
```

### Verify Signature
```bash
openssl dgst -sha256 -verify public.pub -signature signature.bin message.txt
```

## Needed Improvements

### 1. Username Management
- Allow users to set their username
- Store username-key bindings
- Prevent username spoofing
- Allow username changes with signed verification

### 2. Key Management
- Generate unique key pairs per user
- Secure key storage
- Key rotation support
- Key revocation support

### 3. Security Enhancements
- Add timestamp verification
- Implement signature expiration
- Add message encryption
- Add forward secrecy

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

## Future Considerations

### Username Changes
To implement secure username changes:
1. User signs a special message type indicating username change
2. Message includes old and new username
3. Server verifies signature with old username's public key
4. If valid, moves public key to new username file
5. All future messages must use new username

### Multiple Devices
To support multiple devices per user:
1. Implement device registration protocol
2. Allow multiple public keys per username
3. Add device ID to message headers
4. Store device-specific public keys
5. Implement key synchronization

### Message Threading
Current implementation supports basic message threading via `Parent-Message` header. Future improvements could include:
1. Thread signing (sign entire conversation)
2. Thread verification
3. Thread encryption
4. Forward secrecy per thread
