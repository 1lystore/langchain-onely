# Contributing to langchain-onely

Thank you for contributing. This guide outlines how to propose changes and keep the codebase consistent.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## How to Contribute

### Reporting Bugs

1. Check existing issues first.
2. If the issue is new, open a report with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Python version, OS)
   - Relevant error messages or logs

### Suggesting Features

1. Check existing issues and discussions.
2. Open a feature request describing:
   - The problem being solved
   - Proposed solution
   - Alternatives considered
   - User impact

### Pull Requests

1. Create a feature branch.
   ```bash
   git checkout -b feature/your-change
   ```

2. Make changes.
   - Follow the existing style
   - Add docstrings for public functions/classes
   - Include type hints

3. Run quality checks.
   ```bash
   ruff check langchain_onely/
   black --check langchain_onely/
   ```

4. Commit with clear messages.
   ```bash
   git commit -m "feat: describe your change"
   ```

5. Push and open a PR.
   ```bash
   git push origin feature/your-change
   ```

Include a concise description of what changed and why.

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/langchain-onely
cd langchain-onely
pip install -e ".[dev]"
ruff check langchain_onely/
black --check langchain_onely/
black langchain_onely/
```

## Code Style

- Follow PEP 8
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use clear, concise docstrings

## Documentation

- Update `README.md` if adding user-facing features
- Update `CHANGELOG.md` for notable changes
- Add usage examples when introducing new tools

## Security

- Never commit secrets, API keys, or private keys
- Use environment variables for sensitive data
- Report vulnerabilities privately to admin@1ly.store
- Validate all user inputs

## Questions

Open a discussion or email admin@1ly.store.
