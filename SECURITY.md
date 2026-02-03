# Security Policy

## Reporting Security Vulnerabilities

**DO NOT** create a public GitHub issue for security vulnerabilities.

If you discover a security vulnerability, please email us at: **security@catcatai.com**

We will respond within 48 hours and work with you to understand and resolve the issue.

## 🔒 Security Best Practices

### 1. Credentials Management

#### API Keys & OAuth Credentials
- **NEVER** commit API keys, OAuth credentials, or secrets to git
- **NEVER** include `credentials.json` in your commits
- Use `credentials.example.json` as a template
- Store actual credentials in:
  - Environment variables
  - Secure credential managers
  - System keychain

#### Files to NEVER Commit
```
.env
credentials.json
**/credentials.json
token.json
*_token.json
*.pem
*.key
secret.key
api_key.txt
```

### 2. Setting Up Your Own Credentials

#### Google Drive API (Required for File Operations)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Drive API
4. Create OAuth 2.0 credentials
5. Download `client_secret.json`
6. Rename to `credentials.json` and place in `apps/backend/config/`
7. **DO NOT** commit this file!

Example template: `apps/backend/config/credentials.example.json`

### 3. Environment Variables

Create a `.env` file (automatically ignored by git):

```bash
# LLM API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Database
DATABASE_URL=your_database_url

# Other Services
ELEVENLABS_API_KEY=your_key_here
```

### 4. Pre-Commit Checks

Before committing:
```bash
# Check what you're about to commit
git status

# Review changes
git diff --cached

# Ensure no credentials are staged
grep -r "AIzaSy" . --include="*.json" --include="*.env"
```

### 5. Rotating Exposed Credentials

If credentials are accidentally exposed:

1. **Immediately revoke** the exposed credentials
2. Generate new credentials
3. Update local files
4. If committed to git, consider [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) or `git filter-branch`

## 🛡️ Security Features in Angela AI

### Data Protection
- User data stored locally by default
- No cloud storage without explicit configuration
- Conversation history encrypted at rest

### Sandboxing
- Desktop interactions are sandboxed
- File system access limited to specific directories
- Browser automation runs in isolated contexts

### Privacy
- No telemetry or analytics without consent
- No data sent to external services without user knowledge
- Local-first architecture

## ⚠️ Known Security Considerations

### Desktop Automation
Angela AI can:
- Control mouse and keyboard
- Access files in allowed directories
- Take screenshots
- Control browser

**Mitigations:**
- All actions logged to `logs/security.log`
- User confirmation required for sensitive operations
- Sandbox mode available for testing

### Network Access
- Web browsing capabilities
- API calls to configured services
- File downloads/uploads

**Mitigations:**
- Whitelist-based URL filtering
- Rate limiting on external requests
- Content filtering for downloads

## 🔐 Secure Deployment

### Production Checklist
- [ ] All default credentials changed
- [ ] Debug mode disabled
- [ ] Logging configured properly
- [ ] Firewall rules configured
- [ ] Regular security updates applied
- [ ] Backup strategy in place

### Docker Deployment
```dockerfile
# Never bake credentials into images
# Use environment variables or secrets management
ENV CREDENTIALS_PATH=/run/secrets/credentials
```

## 📞 Contact

- Security Issues: security@catcatai.com
- General Questions: support@catcatai.com
- GitHub Issues: For non-security bugs only

## 📜 License & Liability

This project is provided as-is. Users are responsible for:
- Securing their own deployments
- Managing their own API credentials
- Complying with third-party API terms of service
- Ensuring safe use of desktop automation features

---

**Remember: Security is everyone's responsibility!**
