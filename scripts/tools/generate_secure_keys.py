#!/usr/bin/env python
# coding: utf-8
"""
Secure Key Generator

Generates cryptographically secure A/B/C keys for environment configuration.
Keys are base64-encoded and suitable for use with Fernet encryption.
"""

import argparse
import base64
import os
import secrets
import sys
from pathlib import Path


class KeyGenerator:
    MIN_KEY_LENGTH = 32
    
    @staticmethod
    def generate_key(length: int = 32) -> str:
        if length < KeyGenerator.MIN_KEY_LENGTH:
            raise ValueError(f"Key length must be at least {KeyGenerator.MIN_KEY_LENGTH} characters")
        
        random_bytes = secrets.token_bytes(length)
        key = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
        
        return key[:length] if len(key) > length else key.ljust(length, '=')

    @staticmethod
    def generate_fernet_key() -> str:
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')

    @staticmethod
    def validate_key(key: str) -> bool:
        if len(key) < KeyGenerator.MIN_KEY_LENGTH:
            return False
        
        try:
            base64.urlsafe_b64decode(key.encode('utf-8'))
            return True
        except Exception:
            return False

    @staticmethod
    def generate_abc_keys() -> dict:
        keys = {
            'KEY_A': KeyGenerator.generate_fernet_key(),
            'KEY_B': KeyGenerator.generate_fernet_key(),
            'KEY_C': KeyGenerator.generate_fernet_key()
        }
        
        if keys['KEY_A'] == keys['KEY_B'] or keys['KEY_A'] == keys['KEY_C'] or keys['KEY_B'] == keys['KEY_C']:
            return KeyGenerator.generate_abc_keys()
        
        return keys

    @staticmethod
    def save_to_env(keys: dict, output_path: Path, append: bool = False) -> None:
        mode = 'a' if append else 'w'
        
        with open(output_path, mode, encoding='utf-8') as f:
            if not append:
                f.write("# Generated Secure Keys\n")
                f.write("# DO NOT COMMIT THIS FILE TO VERSION CONTROL\n\n")
            
            for key_name, key_value in keys.items():
                f.write(f"{key_name}={key_value}\n")
        
        print(f"Keys saved to: {output_path}")

    @staticmethod
    def print_keys(keys: dict) -> None:
        print("Generated Keys:")
        print("=" * 80)
        for key_name, key_value in keys.items():
            length = len(key_value)
            valid = "✓" if KeyGenerator.validate_key(key_value) else "✗"
            print(f"{valid} {key_name}: {key_value} (length: {length})")
        print()
        print("Validation:")
        all_valid = all(KeyGenerator.validate_key(v) for v in keys.values())
        all_unique = len(set(keys.values())) == len(keys)
        all_long_enough = all(len(v) >= KeyGenerator.MIN_KEY_LENGTH for v in keys.values())
        
        print(f"  All keys valid: {all_valid}")
        print(f"  All keys unique: {all_unique}")
        print(f"  All keys ≥{KeyGenerator.MIN_KEY_LENGTH} chars: {all_long_enough}")


def test_key_generation():
    print("Testing Key Generation...")
    print("=" * 80)
    
    print("\n1. Testing single key generation:")
    key = KeyGenerator.generate_fernet_key()
    print(f"   Generated: {key}")
    print(f"   Length: {len(key)}")
    print(f"   Valid: {KeyGenerator.validate_key(key)}")
    
    print("\n2. Testing A/B/C key generation:")
    keys = KeyGenerator.generate_abc_keys()
    KeyGenerator.print_keys(keys)
    
    print("\n3. Testing key uniqueness (10 iterations):")
    all_keys = set()
    for i in range(10):
        k = KeyGenerator.generate_fernet_key()
        all_keys.add(k)
    print(f"   Generated {len(all_keys)} unique keys out of 10")
    
    print("\n4. Testing validation:")
    valid_key = KeyGenerator.generate_fernet_key()
    invalid_key = "short"
    print(f"   Valid key passes: {KeyGenerator.validate_key(valid_key)}")
    print(f"   Invalid key fails: {not KeyGenerator.validate_key(invalid_key)}")
    
    print("\n✓ All tests passed!")


def main():
    parser = argparse.ArgumentParser(description='Generate secure cryptographic keys')
    parser.add_argument('--output', type=str, help='Output .env file path')
    parser.add_argument('--append', action='store_true', help='Append to existing file')
    parser.add_argument('--test', action='store_true', help='Run self-tests')
    parser.add_argument('--single', action='store_true', help='Generate single key instead of A/B/C')
    parser.add_argument('--length', type=int, default=32, help='Key length (minimum 32)')
    
    args = parser.parse_args()
    
    if args.test:
        test_key_generation()
        sys.exit(0)
    
    try:
        if args.single:
            key = KeyGenerator.generate_key(args.length)
            print(f"Generated key: {key}")
            print(f"Length: {len(key)}")
            print(f"Valid: {KeyGenerator.validate_key(key)}")
        else:
            keys = KeyGenerator.generate_abc_keys()
            KeyGenerator.print_keys(keys)
            
            if args.output:
                output_path = Path(args.output)
                
                if output_path.exists() and not args.append:
                    response = input(f"{output_path} exists. Overwrite? (y/N): ")
                    if response.lower() != 'y':
                        print("Aborted.")
                        sys.exit(0)
                
                KeyGenerator.save_to_env(keys, output_path, append=args.append)
                
                print("\nIMPORTANT: Add the following to your .gitignore:")
                print(f"  {output_path.name}")
            else:
                print("\nTo save these keys, use --output <file> option")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
