# Configuration Directory

This directory contains configuration files for Angela AI.

## ⚠️ IMPORTANT: Credentials Management

### `credentials.json` - DO NOT COMMIT!

The `credentials.json` file contains sensitive OAuth credentials for Google Drive API access. **This file must NEVER be committed to git.**

### Setup Instructions

1. **Get Google Drive API Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google Drive API
   - Create OAuth 2.0 credentials
   - Download the client secrets file

2. **Install Credentials:**
   ```bash
   # Option 1: Copy to system config directory (RECOMMENDED)
   mkdir -p ~/.config/angela-ai
   cp /path/to/downloaded/client_secret.json ~/.config/angela-ai/credentials.json
   
   # Option 2: Copy to project config directory (NOT RECOMMENDED for production)
   cp /path/to/downloaded/client_secret.json apps/backend/config/credentials.json
   ```

3. **Verify .gitignore:**
   Ensure `.gitignore` contains:
   ```
   **/credentials.json
   ```

### File Locations

The application will search for credentials in this order:

1. `~/.config/angela-ai/credentials.json` (System config - RECOMMENDED)
2. `~/.angela/credentials.json` (Alternative location)
3. `apps/backend/config/credentials.json` (Project directory - Development only)
4. Environment variable: `GOOGLE_CREDENTIALS_PATH`

### Template

See `credentials.example.json` for the expected format.

### Security Check

Before committing, run:
```bash
git status | grep credentials
# Should return nothing
```

If credentials.json appears in the output, **DO NOT COMMIT**.

## Other Configuration Files

- `*.yaml`, `*.yml` - Application configuration
- `*.json` - Various settings (excluding credentials.json)
- `requirements*.txt` - Python dependencies

## See Also

- [Security Policy](../../SECURITY.md)
- [Contributing Guide](../../CONTRIBUTING.md)
- [Setup Guide](../../README.md)
