---
name: Bug Report
about: Report a bug to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:

1. Set configuration to '...'
2. Call endpoint '...'
3. Send payload '...'
4. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

What actually happened instead.

## Error Messages

```
Paste any error messages or stack traces here
```

## Environment

**System Information:**
- OS: [e.g., Ubuntu 22.04, macOS 13.0, Windows 11]
- Python Version: [e.g., 3.10.8]
- Docker Version (if applicable): [e.g., 24.0.5]

**Package Versions:**
```bash
# Output of: pip list | grep -E "(fastapi|pydantic|openai|anthropic)"
fastapi==0.104.1
pydantic==2.5.0
openai==1.6.1
anthropic==0.25.1
```

**Configuration:**
```bash
# Relevant .env settings (DO NOT include secrets!)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo
DEBUG=True
```

## Logs

<details>
<summary>Click to expand logs</summary>

```
Paste relevant log output here
```

</details>

## Screenshots

If applicable, add screenshots to help explain your problem.

## Additional Context

Add any other context about the problem here:
- When did this start happening?
- Does it happen consistently or intermittently?
- Have you made any recent changes?
- Does it work in development but not production?

## Possible Solution

If you have ideas on how to fix the issue, please describe them here.

## Related Issues

- Link to related issues if any
