# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of ELAAOMS seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:
- **Email:** security@example.com (replace with actual contact)

### What to Include

Please include the following information in your report:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** of the vulnerability
4. **Suggested fix** (if you have one)
5. **Your contact information** for follow-up

### Response Timeline

- **Initial Response:** Within 48 hours
- **Status Update:** Within 5 business days
- **Fix Timeline:** Depends on severity (see below)

### Severity Levels

| Severity | Description | Fix Timeline |
|----------|-------------|--------------|
| **Critical** | Remote code execution, authentication bypass, data breach | 24-48 hours |
| **High** | Privilege escalation, SQL injection, XSS | 1 week |
| **Medium** | Information disclosure, DoS | 2 weeks |
| **Low** | Minor security improvements | Next release |

## Security Best Practices

### For Users

When deploying ELAAOMS, please follow these security best practices:

#### 1. HMAC Secret Management

```bash
# Generate a strong HMAC secret
openssl rand -hex 32

# Never commit secrets to git
echo "*.env" >> .gitignore
```

#### 2. API Key Security

```bash
# Store API keys securely
# Use environment variables, not hardcoded values
ELEVENLABS_API_KEY=your_secret_key_here
LLM_API_KEY=your_secret_key_here

# Never log API keys
logger.info(f"Using API key: {api_key[:8]}...")  # Only show first 8 chars
```

#### 3. HTTPS Configuration

```nginx
# Always use HTTPS in production
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
    }
}
```

#### 4. Database Security

```yaml
# Use strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Restrict database access
# Only allow connections from application server
```

#### 5. Rate Limiting

```python
# Implement rate limiting to prevent abuse
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/webhook/post-call")
@limiter.limit("100/minute")
async def receive_webhook(...):
    ...
```

#### 6. Input Validation

```python
# Always validate input
from pydantic import BaseModel, validator

class SecurePayload(BaseModel):
    field: str

    @validator('field')
    def validate_field(cls, v):
        # Sanitize input
        if len(v) > 1000:
            raise ValueError("Field too long")
        return v
```

### For Developers

#### 1. Code Review

- All code changes require review before merging
- Security-sensitive changes require review by security team
- Use automated security scanning tools

#### 2. Dependency Management

```bash
# Regularly update dependencies
pip list --outdated

# Check for known vulnerabilities
pip-audit

# Use dependabot for automated updates
```

#### 3. Secrets Scanning

```bash
# Scan for accidentally committed secrets
git secrets --scan

# Use pre-commit hooks
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    hooks:
      - id: detect-secrets
```

#### 4. Security Testing

```bash
# Run security tests
pytest tests/security/

# Perform penetration testing before major releases
# Use tools like OWASP ZAP, Burp Suite
```

## Known Security Considerations

### 1. HMAC Signature Validation

**Implementation:** `app/auth.py`

The system uses HMAC-SHA256 to validate webhook signatures. This prevents:
- Unauthorized webhook calls
- Request tampering
- Replay attacks (via timestamp validation)

**Security Notes:**
- Signatures expire after 30 minutes
- Constant-time comparison prevents timing attacks
- Secret key should be at least 32 bytes

### 2. Memory Data Storage

**Implementation:** OpenMemory storage

Conversation memories may contain sensitive information:
- Customer data (names, phone numbers, emails)
- Order information
- Personal preferences
- Private conversation details

**Recommendations:**
- Implement data retention policies
- Consider encryption at rest
- Comply with GDPR/CCPA requirements
- Provide data deletion mechanisms

### 3. LLM API Keys

**Implementation:** LLM service integration

API keys for OpenAI/Anthropic have access to:
- LLM models
- Usage billing
- Conversation data

**Recommendations:**
- Rotate keys regularly
- Use separate keys for development/production
- Monitor usage for anomalies
- Implement spending limits

### 4. OpenMemory Access

**Implementation:** OpenMemory client

OpenMemory stores all conversation memories:
- Implement authentication if exposed
- Use network segmentation
- Regular backups
- Access logging

## Security Features

### ✅ Implemented

- [x] HMAC-SHA256 webhook signature validation
- [x] Timestamp-based replay attack prevention
- [x] Input validation using Pydantic models
- [x] Structured logging for audit trails
- [x] Environment-based configuration (no hardcoded secrets)
- [x] CORS configuration
- [x] Request ID tracking
- [x] Error handling without information disclosure

### 🔄 Recommended (Not Implemented)

- [ ] Rate limiting on API endpoints
- [ ] API key rotation mechanism
- [ ] Data encryption at rest
- [ ] Audit logging for memory access
- [ ] IP whitelisting for webhooks
- [ ] WAF (Web Application Firewall) integration
- [ ] Secrets management (e.g., HashiCorp Vault)
- [ ] Automated vulnerability scanning in CI/CD

## Vulnerability Disclosure Policy

We follow a **responsible disclosure** policy:

1. **Report** the vulnerability privately
2. **Wait** for initial response (48 hours)
3. **Collaborate** on a fix
4. **Coordinate** public disclosure
5. **Credit** given to reporter (if desired)

### Timeline

- **Day 0:** Vulnerability reported
- **Day 2:** Initial response sent
- **Day 7:** Fix developed and tested
- **Day 14:** Patch released
- **Day 30:** Public disclosure (if appropriate)

## Security Updates

Security updates are released as patch versions (e.g., 1.0.1, 1.0.2).

### How to Stay Updated

1. **Watch this repository** for security advisories
2. **Subscribe to notifications** for new releases
3. **Review CHANGELOG.md** for security fixes
4. **Apply updates promptly** in production

### Checking Your Version

```bash
# Check installed version
grep APP_VERSION .env

# Or check in code
python -c "from config.settings import get_settings; print(get_settings().app_version)"
```

## Security Checklist for Production

Before deploying to production, verify:

- [ ] HTTPS enabled with valid SSL certificate
- [ ] HMAC secret key is strong and unique
- [ ] API keys stored securely (not in code)
- [ ] Database password is strong
- [ ] OpenMemory is behind firewall/VPN
- [ ] Rate limiting configured
- [ ] Logging configured (but no sensitive data logged)
- [ ] Regular backups configured
- [ ] Monitoring and alerting configured
- [ ] Security headers configured (HSTS, etc.)
- [ ] Dependencies up to date
- [ ] Vulnerability scanning enabled
- [ ] Incident response plan in place

## Compliance

### GDPR Compliance

If processing EU citizen data:

1. **Data Minimization:** Only store necessary memories
2. **Right to Erasure:** Implement memory deletion
3. **Data Portability:** Provide memory export
4. **Consent:** Inform users about memory storage
5. **Data Protection:** Encrypt sensitive data

### CCPA Compliance

If processing California resident data:

1. **Disclosure:** Inform users about data collection
2. **Access:** Provide access to stored memories
3. **Deletion:** Allow users to delete their data
4. **Opt-Out:** Provide opt-out mechanism

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

## Contact

For security concerns:
- **Email:** security@example.com
- **PGP Key:** (provide if available)

For general questions:
- **GitHub Issues:** https://github.com/webmasterarbez/elaaoms_claude/issues
- **Documentation:** See README.md

---

**Last Updated:** 2025-11-13
**Version:** 1.0.0
