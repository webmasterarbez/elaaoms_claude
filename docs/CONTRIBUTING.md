# Contributing to ELAAOMS

Thank you for your interest in contributing to the ElevenLabs Agents Universal Agentic Open Memory System (ELAAOMS)! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. By participating, you are expected to uphold this code. Please be respectful and professional in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/elaaoms_claude.git
   cd elaaoms_claude
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/webmasterarbez/elaaoms_claude.git
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- Git
- Your favorite code editor (VS Code, PyCharm, etc.)

### Local Environment

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start OpenMemory**:
   ```bash
   docker run -d -p 8080:8080 caviraoss/openmemory:latest
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug fixes** - Fix issues in the codebase
- **New features** - Add new functionality
- **Documentation** - Improve or add documentation
- **Tests** - Add or improve test coverage
- **Code quality** - Refactor code, improve performance
- **Examples** - Add usage examples or tutorials

### Contribution Workflow

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number-description
   ```

2. **Make your changes** following our [coding standards](#coding-standards)

3. **Test your changes** thoroughly

4. **Commit your changes** with clear commit messages:
   ```bash
   git add .
   git commit -m "Add feature: description of changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 100 characters maximum
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Imports**: Organized in three groups (standard library, third-party, local)

### Code Quality

- **Type hints**: Use type hints for function parameters and return values
- **Docstrings**: All functions and classes must have docstrings
- **Comments**: Add comments for complex logic
- **Logging**: Use appropriate logging levels (DEBUG, INFO, WARNING, ERROR)

### Example Code Style

```python
from typing import List, Dict, Optional
from datetime import datetime, timezone


class MyClass:
    """Brief description of the class.

    Longer description if needed.

    Attributes:
        attribute_name: Description of attribute
    """

    def my_method(self, param1: str, param2: int) -> Optional[Dict[str, Any]]:
        """Brief description of what this method does.

        Args:
            param1: Description of param1
            param2: Description of param2

        Returns:
            Description of return value

        Raises:
            ValueError: Description of when this is raised
        """
        logger.info(f"Processing {param1} with value {param2}")

        try:
            # Implementation here
            result = {"key": "value"}
            return result
        except Exception as e:
            logger.error(f"Error in my_method: {e}", exc_info=True)
            return None
```

### File Organization

```
app/
├── __init__.py          # App initialization
├── models.py            # Pydantic models
├── routes.py            # API endpoints
├── services/            # Business logic
│   ├── llm_service.py
│   └── openmemory_client.py
└── utils/               # Utility functions
```

## Testing

### Writing Tests

- Place tests in the `tests/` directory
- Use `pytest` for testing
- Aim for >80% code coverage
- Test both success and failure cases

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_routes.py

# Run specific test
pytest tests/test_routes.py::test_health_check
```

### Test Example

```python
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_webhook_with_invalid_signature():
    """Test webhook with invalid HMAC signature."""
    response = client.post(
        "/webhook/post-call",
        json={"type": "post_call_transcription", "data": {}},
        headers={"elevenlabs-signature": "invalid"}
    )
    assert response.status_code == 401
```

## Pull Request Process

### Before Submitting

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass** locally
4. **Update CHANGELOG.md** with your changes
5. **Rebase on latest main** if needed:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

### PR Guidelines

1. **Title**: Use a clear, descriptive title
   - ✅ "Add support for Anthropic Claude LLM provider"
   - ❌ "Update code"

2. **Description**: Include:
   - What changes were made
   - Why the changes were needed
   - How to test the changes
   - Screenshots (if UI changes)
   - Related issue numbers

3. **Size**: Keep PRs focused and reasonably sized
   - Large PRs are harder to review
   - Consider breaking into multiple PRs

4. **Commits**:
   - Use clear commit messages
   - Squash commits if needed for clarity

### PR Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## How Has This Been Tested?
Describe the testing you've done

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] CHANGELOG.md updated
```

### Review Process

- All PRs require at least one review
- Address review comments promptly
- Be respectful and constructive in discussions
- Maintainers may request changes before merging

## Reporting Bugs

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Test on latest version** to ensure bug still exists
3. **Gather information** about the bug

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Set configuration to '...'
2. Call endpoint '....'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.10.8]
- Package versions: [from pip freeze]

**Logs**
```
Relevant log output
```

**Additional context**
Any other information about the problem.
```

## Suggesting Enhancements

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
What you want to happen.

**Describe alternatives you've considered**
Other solutions or features you've considered.

**Additional context**
Any other context, mockups, or examples.
```

## Development Best Practices

### Git Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(memory): add deduplication logic for extracted memories

Implement similarity checking to prevent storing duplicate
memories for the same conversation.

Closes #123
```

```
fix(hmac): correct timestamp comparison in signature validation

The timestamp comparison was using timezone-naive datetime which
caused validation failures. Now using timezone-aware datetime.

Fixes #456
```

### Code Review Guidelines

**For Authors:**
- Respond to all comments
- Ask for clarification if needed
- Be open to feedback
- Update PR based on feedback

**For Reviewers:**
- Be constructive and respectful
- Explain the "why" behind suggestions
- Approve when ready, request changes when needed
- Test the changes if possible

## Questions?

If you have questions about contributing:

1. Check existing documentation
2. Search closed issues
3. Ask in discussions
4. Open a new issue with the `question` label

## License

By contributing to ELAAOMS, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to ELAAOMS! 🚀
