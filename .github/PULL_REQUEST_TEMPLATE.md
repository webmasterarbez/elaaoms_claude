# Pull Request

## Description

<!-- Provide a clear and concise description of your changes -->

## Type of Change

<!-- Mark the relevant option with an [x] -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Test coverage improvement
- [ ] Build/CI configuration change

## Related Issue

<!-- Link to the issue this PR addresses -->

Fixes #(issue number)
Closes #(issue number)
Relates to #(issue number)

## Motivation and Context

<!-- Why is this change required? What problem does it solve? -->

## Changes Made

<!-- Detailed list of changes -->

- Change 1
- Change 2
- Change 3

## How Has This Been Tested?

<!-- Describe the tests you ran to verify your changes -->

**Test Configuration:**
- OS: [e.g., Ubuntu 22.04]
- Python Version: [e.g., 3.10.8]
- Test Environment: [e.g., Docker, local development]

**Test Cases:**
- [ ] Test case 1: Description
- [ ] Test case 2: Description
- [ ] Manual testing performed
- [ ] Automated tests added/updated

**Test Commands:**
```bash
# Commands used to test
pytest tests/
python -m pytest tests/test_specific.py
```

**Test Results:**
```
# Paste test output here (if relevant)
```

## Screenshots (if appropriate)

<!-- Add screenshots to demonstrate visual changes -->

## Checklist

<!-- Mark completed items with an [x] -->

### Code Quality

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings or errors
- [ ] I have checked for and removed any console.log() or debugging code

### Documentation

- [ ] I have updated the documentation accordingly
- [ ] I have updated the CHANGELOG.md file
- [ ] I have added/updated docstrings for new/modified functions
- [ ] README.md is updated (if needed)
- [ ] API documentation is updated (if needed)

### Testing

- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have tested edge cases and error conditions
- [ ] I have tested with different configurations (if applicable)

### Dependencies

- [ ] Any new dependencies are documented in requirements.txt
- [ ] I have checked that new dependencies are necessary
- [ ] New dependencies are from trusted sources
- [ ] License compatibility verified for new dependencies

### Security

- [ ] I have reviewed my code for security vulnerabilities
- [ ] No sensitive information (API keys, passwords) is committed
- [ ] Input validation is implemented for new endpoints
- [ ] HMAC signature validation is maintained for webhooks (if applicable)

### Performance

- [ ] I have considered the performance impact of my changes
- [ ] Database queries are optimized (if applicable)
- [ ] No unnecessary API calls added
- [ ] Memory usage is reasonable

### Breaking Changes

- [ ] This PR does not introduce breaking changes
- **OR** Breaking changes are documented below:

<!-- If there are breaking changes, describe them: -->
**Breaking Changes:**
-

**Migration Guide:**
-

## Additional Notes

<!-- Any additional information reviewers should know -->

## Reviewer Checklist

<!-- For reviewers - mark items as you review -->

- [ ] Code follows project conventions
- [ ] Changes are well-tested
- [ ] Documentation is clear and complete
- [ ] No obvious bugs or issues
- [ ] Performance impact is acceptable
- [ ] Security considerations addressed
- [ ] Ready to merge

---

**By submitting this pull request, I confirm that my contribution is made under the terms of the MIT License.**
