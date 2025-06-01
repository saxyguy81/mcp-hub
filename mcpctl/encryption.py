"""
MCP Hub Encryption Manager
Handles symmetric encryption of secrets using user-provided keys
"""

import base64
import getpass
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    print(
        "Warning: cryptography library not found. Install with: pip install cryptography"
    )
    Fernet = None


class EncryptionManager:
    """Manages encryption/decryption of MCP Hub secrets"""

    def __init__(self):
        self.key_cache = None
        self.salt_file = Path.home() / ".mcpctl" / "salt"

    def derive_key_from_password(
        self, password: str, salt: bytes = None
    ) -> Tuple[bytes, bytes]:
        """Derive encryption key from password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    def get_or_create_salt(self) -> bytes:
        """Get existing salt or create new one"""
        if self.salt_file.exists():
            with open(self.salt_file, "rb") as f:
                return f.read()
        else:
            salt = os.urandom(16)
            self.salt_file.parent.mkdir(exist_ok=True)
            with open(self.salt_file, "wb") as f:
                f.write(salt)
            return salt

    def prompt_for_key(self, workspace_name: str = "") -> str:
        """Prompt user for encryption key"""
        prompt = (
            f"🔐 Enter encryption key for workspace '{workspace_name}': "
            if workspace_name
            else "🔐 Enter encryption key: "
        )
        return getpass.getpass(prompt)

    def get_key_from_lastpass(self, workspace_name: str) -> Optional[str]:
        """Retrieve encryption key from LastPass"""
        try:
            from .secret_backends.lastpass import LastPassBackend

            backend = LastPassBackend()
            key_name = f"mcp-hub-encryption-{workspace_name}"
            return backend.get_secret(key_name)
        except Exception as e:
            print(f"Warning: Could not retrieve key from LastPass: {e}")
            return None

    def store_key_in_lastpass(self, workspace_name: str, key: str) -> bool:
        """Store encryption key in LastPass"""
        try:
            from .secret_backends.lastpass import LastPassBackend

            backend = LastPassBackend()
            key_name = f"mcp-hub-encryption-{workspace_name}"
            backend.set_secret(key_name, key)
            return True
        except Exception as e:
            print(f"Warning: Could not store key in LastPass: {e}")
            return False

    def get_encryption_key(
        self, workspace_name: str, use_lastpass: bool = True
    ) -> bytes:
        """Get encryption key via LastPass or user prompt"""
        if self.key_cache:
            return self.key_cache

        key_password = None

        # Try LastPass first if enabled
        if use_lastpass:
            key_password = self.get_key_from_lastpass(workspace_name)
            if key_password:
                print(f"✅ Retrieved encryption key from LastPass")

        # Prompt user if LastPass failed or disabled
        if not key_password:
            key_password = self.prompt_for_key(workspace_name)

            # Offer to store in LastPass
            if use_lastpass:
                store = (
                    input("💾 Store this key in LastPass for future use? (y/N): ")
                    .lower()
                    .startswith("y")
                )
                if store:
                    if self.store_key_in_lastpass(workspace_name, key_password):
                        print("✅ Key stored in LastPass")

        # Derive encryption key from password
        salt = self.get_or_create_salt()
        key, _ = self.derive_key_from_password(key_password, salt)

        # Cache for session
        self.key_cache = key
        return key

    def encrypt_data(
        self, data: Dict[str, Any], workspace_name: str, use_lastpass: bool = True
    ) -> str:
        """Encrypt dictionary data to base64 string"""
        if not Fernet:
            raise RuntimeError("cryptography library required for encryption")

        key = self.get_encryption_key(workspace_name, use_lastpass)
        fernet = Fernet(key)

        # Convert data to JSON and encrypt
        json_data = json.dumps(data, sort_keys=True)
        encrypted_data = fernet.encrypt(json_data.encode())

        # Return base64 encoded for safe text storage
        return base64.b64encode(encrypted_data).decode()

    def decrypt_data(
        self, encrypted_string: str, workspace_name: str, use_lastpass: bool = True
    ) -> Dict[str, Any]:
        """Decrypt base64 string back to dictionary data"""
        if not Fernet:
            raise RuntimeError("cryptography library required for decryption")

        key = self.get_encryption_key(workspace_name, use_lastpass)
        fernet = Fernet(key)

        try:
            # Decode from base64 and decrypt
            encrypted_data = base64.b64decode(encrypted_string.encode())
            decrypted_data = fernet.decrypt(encrypted_data)

            # Parse JSON back to dictionary
            return json.loads(decrypted_data.decode())

        except Exception as e:
            raise RuntimeError(f"Failed to decrypt data (wrong key?): {e}")

    def encrypt_secrets(
        self, secrets: Dict[str, str], workspace_name: str, use_lastpass: bool = True
    ) -> str:
        """Encrypt secrets dictionary"""
        return self.encrypt_data(secrets, workspace_name, use_lastpass)

    def decrypt_secrets(
        self, encrypted_secrets: str, workspace_name: str, use_lastpass: bool = True
    ) -> Dict[str, str]:
        """Decrypt secrets dictionary"""
        return self.decrypt_data(encrypted_secrets, workspace_name, use_lastpass)

    def test_encryption(self, workspace_name: str = "test") -> bool:
        """Test encryption/decryption cycle"""
        test_data = {
            "OPENAI_API_KEY": "sk-test-key-12345",
            "DATABASE_PASSWORD": "super-secret-password",
            "API_TOKEN": "bearer-token-xyz",
        }

        try:
            # Encrypt
            encrypted = self.encrypt_data(test_data, workspace_name, use_lastpass=False)
            print(f"✅ Encryption successful: {encrypted[:50]}...")

            # Decrypt
            decrypted = self.decrypt_data(encrypted, workspace_name, use_lastpass=False)
            print(f"✅ Decryption successful: {list(decrypted.keys())}")

            # Verify
            if decrypted == test_data:
                print("✅ Encryption test passed!")
                return True
            else:
                print("❌ Encryption test failed: data mismatch")
                return False

        except Exception as e:
            print(f"❌ Encryption test failed: {e}")
            return False

    def clear_key_cache(self):
        """Clear cached encryption key"""
        self.key_cache = None

    def generate_new_key(self) -> str:
        """Generate a new random encryption key"""
        import secrets
        import string

        # Generate a strong random password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(32))

    def export_key_for_sharing(self, workspace_name: str) -> str:
        """Export encryption key in shareable format"""
        # Get the raw password (not derived key)
        if self.get_key_from_lastpass(workspace_name):
            return "Key is stored in LastPass - access via LastPass on new machine"
        else:
            return "Key was entered manually - you'll need to enter it again on new machines"

    def import_key_setup(self, workspace_name: str, key_hint: str = "") -> bool:
        """Setup encryption key when importing workspace"""
        print(f"🔐 Workspace '{workspace_name}' uses encrypted secrets")

        if "LastPass" in key_hint:
            print("💡 This workspace stores its encryption key in LastPass")
            use_lastpass = (
                input("🔑 Try to retrieve key from LastPass? (Y/n): ").lower() != "n"
            )
        else:
            print("💡 This workspace uses a manually entered encryption key")
            use_lastpass = (
                input("🔑 Check LastPass for encryption key? (y/N): ")
                .lower()
                .startswith("y")
            )

        try:
            # This will prompt or fetch from LastPass
            self.get_encryption_key(workspace_name, use_lastpass)
            print("✅ Encryption key configured successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to configure encryption key: {e}")
            return False


class SecureWorkspaceManager:
    """Extended workspace manager with encryption support"""

    def __init__(self):
        from .workspace import WorkspaceManager

        self.workspace_manager = WorkspaceManager()
        self.encryption_manager = EncryptionManager()

    def create_encrypted_workspace(
        self,
        name: str,
        description: str,
        secrets: Dict[str, str],
        services: Dict[str, Any],
        use_lastpass: bool = True,
    ) -> None:
        """Create workspace with encrypted secrets"""

        # Encrypt secrets
        encrypted_secrets = self.encryption_manager.encrypt_secrets(
            secrets, name, use_lastpass
        )

        # Create workspace with encrypted data
        from .workspace import MCPWorkspace

        workspace = MCPWorkspace(
            name=name,
            description=description,
            services=services,
            secrets={"encrypted": True, "data": encrypted_secrets},
            author=os.environ.get("USER", "unknown"),
        )

        self.workspace_manager.save_workspace(workspace)
        print(f"🔐 Created encrypted workspace '{name}'")

    def load_and_decrypt_workspace(
        self, name: str, use_lastpass: bool = True
    ) -> Optional[Dict[str, str]]:
        """Load workspace and decrypt its secrets"""
        workspace = self.workspace_manager.load_workspace(name)
        if not workspace:
            return None

        if isinstance(workspace.secrets, dict) and workspace.secrets.get("encrypted"):
            try:
                encrypted_data = workspace.secrets["data"]
                decrypted_secrets = self.encryption_manager.decrypt_secrets(
                    encrypted_data, name, use_lastpass
                )
                return decrypted_secrets
            except Exception as e:
                print(f"❌ Failed to decrypt secrets: {e}")
                return None
        else:
            # Legacy unencrypted workspace
            return workspace.secrets or {}
