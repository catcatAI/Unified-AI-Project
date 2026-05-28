# Security Key Rotation Procedure

## Overview

Angela AI uses cryptographic keys (ANGELA_KEY_A, ANGELA_KEY_B, ANGELA_KEY_C) for secure communication between components. This document describes the key rotation procedure to maintain security best practices.

## Key Requirements

- **Minimum Length**: 32 characters
- **Format**: Base64-encoded Fernet keys (44 characters recommended)
- **Uniqueness**: All keys (A, B, C) must be unique
- **Generation**: Must use cryptographically secure random generator

## Key Usage

- **ANGELA_KEY_A**: Backend control and internal operations
- **ANGELA_KEY_B**: Mobile communication encryption
- **ANGELA_KEY_C**: Desktop synchronization encryption
- **MIKO_HAM_KEY**: HAM (Hierarchical Associative Memory) storage encryption

## Rotation Procedure

### 1. Generate New Keys

Use the built-in key generator:

```bash
python scripts/tools/generate_secure_keys.py --output new_keys.env
```

This will generate three new secure keys and save them to `new_keys.env`.

### 2. Backup Current Configuration

```bash
# Create backup of current .env
copy .env .env.backup.%date:~-4,4%%date:~-10,2%%date:~-7,2%
```

### 3. Update Environment Configuration

Manually update the keys in `.env`:

```bash
# Open .env in editor and replace:
ANGELA_KEY_A=<new_key_from_new_keys.env>
ANGELA_KEY_B=<new_key_from_new_keys.env>
ANGELA_KEY_C=<new_key_from_new_keys.env>
```

### 4. Validate Configuration

Run the configuration validator to ensure keys are valid:

```bash
python apps/backend/src/core/config_validator.py --env-file .env
```

Expected output:
```
✓ 配置验证通过
```

### 5. Test Keys

Verify keys work for encryption/decryption:

```bash
python test_keys.py
```

All three keys should pass validation.

### 6. Restart Services

Restart all Angela AI services to load new keys:

```bash
# Stop all services
# ... stop commands ...

# Start backend
cd apps/backend
python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000

# Start desktop app
cd apps/desktop-app/electron_app
pnpm start
```

### 7. Verify System Functionality

- Test backend API health endpoint: `http://127.0.0.1:8000/health`
- Test desktop app connection
- Test mobile app connection (if applicable)
- Verify encrypted data can be accessed

### 8. Secure Cleanup

```bash
# Delete temporary key files
del new_keys.env

# Securely delete backup (after confirming system works)
# Keep backup for 7 days in secure location, then delete
```

## Rotation Schedule

- **Development**: Rotate keys monthly
- **Production**: Rotate keys quarterly or immediately if compromised
- **After Security Incident**: Rotate immediately

## Key Compromise Response

If a key is suspected to be compromised:

1. **Immediate Action**: Generate new keys immediately
2. **Emergency Rotation**: Follow rotation procedure above
3. **Audit**: Review access logs for unauthorized access
4. **Notification**: Notify security team and affected users
5. **Investigation**: Determine compromise vector and remediate

## Security Best Practices

1. **Never commit keys to version control**: `.env` is in `.gitignore`
2. **Store backups securely**: Use encrypted storage for backups
3. **Limit access**: Only authorized personnel should have key access
4. **Monitor usage**: Log and monitor key usage patterns
5. **Use different keys per environment**: Development, staging, production should have unique keys
6. **Document changes**: Record key rotation dates in security log

## Troubleshooting

### "Invalid key" Error

- Verify key length ≥32 characters
- Check for whitespace or special characters
- Ensure key is base64-encoded

### "Keys not unique" Error

- Regenerate keys using the key generator
- Never reuse keys from other environments

### Backend Won't Start

- Run config validator: `python apps/backend/src/core/config_validator.py --env-file .env`
- Check for syntax errors in `.env`
- Verify all required keys are present

## Additional Resources

- Key Generator: `scripts/tools/generate_secure_keys.py`
- Config Validator: `apps/backend/src/core/config_validator.py`
- Security Documentation: `docs/security/`

## Emergency Contacts

- Security Team: [Contact information]
- DevOps Team: [Contact information]
- On-call Engineer: [Contact information]
