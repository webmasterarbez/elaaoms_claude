# ELAAOMS Development Constitution

## Project Purpose

A universal memory system for ElevenLabs AI agents that automatically extracts, stores, and retrieves conversation memories across all your agents. Provides personalized greetings for returning callers and real-time memory search during calls.

## Core Principles

### Professional Conduct

- Maintain respectful and professional interactions in all contributions
- Provide constructive feedback during code reviews
- Collaborate openly and transparently

### Contribution Values

- **Quality over quantity**: Focused, well-tested changes preferred
- **Documentation-first**: All changes must include relevant documentation
- **Security-conscious**: Consider security implications in all development
- **User-centric**: Prioritize features that enhance memory system reliability

### Types of Accepted Contributions

- Bug fixes addressing issues in the codebase
- New features adding functionality to memory system
- Documentation improvements and additions
- Test coverage additions and improvements
- Code quality refactoring and performance optimization

## Development Standards

### Python Code Style (PEP 8 Modified)

- **Line length**: 100 characters maximum
- **Indentation**: 4 spaces, no tabs
- **Quotes**: Double quotes for strings
- **Imports**: Organized in three groups (standard library, third-party, local)

### Code Quality Requirements

- **Type hints**: Required for all function parameters and return values
- **Docstrings**: Mandatory for all functions and classes
- **Comments**: Required for complex logic
- **Logging**: Use appropriate levels (DEBUG, INFO, WARNING, ERROR)
- **Error handling**: Comprehensive try-except with proper logging

### File Organization Pattern

```
app/
├── __init__.py          # App initialization
├── models.py            # Pydantic models
├── routes.py            # API endpoints
├── services/            # Business logic
└── utils/               # Utility functions
```

### Testing Requirements

- Place tests in `tests/` directory
- Use pytest framework
- Maintain >80% code coverage
- Test both success and failure cases
- Test security-sensitive code paths

### Commit Message Format (Conventional Commits)

```
<type>(<scope>): <subject>
```

**Types**: feat, fix, docs, style, refactor, test, chore

### Pull Request Requirements

- Clear, descriptive title
- Detailed description including rationale and testing approach
- All tests passing
- Documentation updated
- CHANGELOG.md updated
- Focused scope (avoid large, unfocused PRs)
- At least one review required before merge

## Security Requirements

### Critical Security Rules

- **Never commit secrets**: API keys, HMAC secrets, passwords stay out of version control
- **HMAC validation**: All webhooks must validate HMAC-SHA256 signatures
- **Input validation**: All inputs validated using Pydantic models
- **HTTPS only**: Production deployments require HTTPS with valid certificates
- **No information disclosure**: Error messages must not leak sensitive data

### API Key Management

- Store API keys in environment variables only
- Never log full API keys (maximum first 8 characters)
- Rotate keys regularly
- Use separate keys for development and production
- Monitor usage for anomalies

### Webhook Security

- HMAC-SHA256 signature validation mandatory
- Timestamp validation (30-minute window)
- Constant-time comparison to prevent timing attacks
- HMAC secrets must be minimum 32 bytes

### Data Protection

- Conversation memories contain PII (phone numbers, names, preferences)
- Implement data retention policies
- Consider encryption at rest for sensitive data
- Comply with GDPR/CCPA where applicable
- Provide data deletion mechanisms

### Vulnerability Handling

- **Critical vulnerabilities**: Fix within 24-48 hours
- **High severity**: Fix within 1 week
- **Medium severity**: Fix within 2 weeks
- Report security issues privately, never through public GitHub issues

### Required Security Features

- HMAC-SHA256 webhook signature validation
- Timestamp-based replay attack prevention
- Input validation using Pydantic models
- Structured logging for audit trails
- Environment-based configuration
- Request ID tracking
- CORS configuration

## Documentation Rules

### Documentation-Code Alignment

- **Code changes require documentation updates**: No exceptions
- **Documentation precedes implementation**: Document expected behavior first
- **Keep docs synchronized**: Review and update affected docs with every code change
- **No orphaned documentation**: Remove docs when features are removed

### Required Documentation

- Docstrings for all public functions and classes
- API endpoint documentation with request/response examples
- Configuration variable descriptions in README
- Security considerations for new features
- Architecture decisions documented when patterns change

### Documentation Quality Standards

- Clear, concise language
- Practical examples included
- Version-specific information clearly marked
- Cross-references maintained between related docs
- Security implications explicitly stated

### Documentation Types

- **README.md**: Project overview, quick start, API reference
- **CONTRIBUTING.md**: Development guidelines and standards
- **SECURITY.md**: Security policies and best practices
- **DEPLOYMENT.md**: Production deployment instructions
- **CHANGELOG.md**: Version history with security notes

### Documentation Maintenance

- Update documentation in the same PR as code changes
- Verify all links and references are current
- Review documentation during code review process
- Archive outdated documentation, never delete (maintain history)

---

**Last Updated**: 2025-11-13
**Version**: 1.0.0
**Status**: Active
