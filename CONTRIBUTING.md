# Contributing to Upbit Quant System

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/your-username/upbit-quant-system/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Error messages or logs if applicable

### Suggesting Features

1. Check existing issues and discussions
2. Create a new issue with:
   - Clear description of the feature
   - Use case and motivation
   - Proposed implementation (if you have ideas)

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the coding standards (see below)
   - Write/update tests
   - Update documentation

4. **Run quality checks**
   ```bash
   make check  # Runs all checks (format, lint, type-check, test)
   ```

5. **Commit your changes**
   ```bash
   git commit -m "feat: add new feature"
   ```
   Use conventional commit messages:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test additions/changes
   - `refactor:` Code refactoring
   - `style:` Code style changes (formatting, etc.)

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide clear description
   - Reference related issues
   - Wait for review and feedback

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone your fork
git clone https://github.com/your-username/upbit-quant-system.git
cd upbit-quant-system

# Install dependencies
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all functions
- Write docstrings (Google style)
- Maximum line length: 100 characters

### Code Quality Tools

```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Run tests
make test

# Run all checks
make check
```

### Testing

- Write tests for new features
- Maintain or improve test coverage
- Use pytest fixtures for test data
- Follow naming: `test_*.py` files, `test_*` functions

### Documentation

- Update README.md if needed
- Add docstrings to new functions/classes
- Update relevant documentation files
- Keep comments clear and concise

## Project Structure

```
upbit-quant-system/
├── src/              # Source code
├── tests/            # Test files
├── docs/             # Documentation
├── scripts/          # Utility scripts
└── deploy/           # Deployment files
```

## Commit Message Guidelines

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

Examples:
- `feat(strategy): add momentum filter condition`
- `fix(engine): correct equity calculation bug`
- `docs(readme): update installation instructions`
- `test(cache): add cache invalidation tests`

## Review Process

1. All PRs require at least one review
2. Maintainers will review within 2-3 business days
3. Address review comments promptly
4. Keep PRs focused and reasonably sized

## Questions?

- Open an issue for questions
- Check existing documentation
- Review closed issues/PRs for similar questions

Thank you for contributing! 🎉
