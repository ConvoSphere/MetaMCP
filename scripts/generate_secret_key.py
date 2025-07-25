#!/usr/bin/env python3
"""
Generate Secure Secret Key

This script generates a secure secret key for MetaMCP using bcrypt.
The generated key can be used in the .env file for the SECRET_KEY setting.
"""

import secrets
import string

import bcrypt


def generate_secure_secret_key(length: int = 64) -> str:
    """
    Generate a secure secret key using bcrypt and random characters.

    Args:
        length: Length of the secret key (default: 64)

    Returns:
        A secure secret key string
    """
    # Generate random characters
    characters = string.ascii_letters + string.digits + string.punctuation
    random_string = "".join(secrets.choice(characters) for _ in range(length))

    # Use bcrypt to hash the random string
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(random_string.encode("utf-8"), salt)

    # Convert to hex and truncate to desired length
    secret_key = hashed.hex()[:length]

    return secret_key


def main():
    """Generate and display a secure secret key."""
    print("🔐 Generating secure secret key for MetaMCP...")
    print()

    # Generate the secret key
    secret_key = generate_secure_secret_key()

    print("✅ Secure secret key generated successfully!")
    print()
    print("📋 Add this to your .env file:")
    print(f"SECRET_KEY={secret_key}")
    print()
    print("⚠️  Important security notes:")
    print("- Keep this key secret and secure")
    print("- Never commit it to version control")
    print("- Use different keys for different environments")
    print("- Rotate keys regularly in production")
    print()
    print("🔧 To use this key:")
    print("1. Copy the SECRET_KEY line above")
    print("2. Paste it into your .env file")
    print("3. Restart your MetaMCP application")


if __name__ == "__main__":
    main()
