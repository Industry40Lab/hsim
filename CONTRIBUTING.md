# Contributing to hsim

Thank you for your interest in contributing to hsim! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/hsim.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Commit with clear messages: `git commit -m "Add feature X"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest flake8 black

# Install package in development mode
pip install -e .
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to public functions and classes
- Keep functions focused and concise
- Use type hints where appropriate

### Example

```python
def calculate_utilization(busy_time: float, total_time: float) -> float:
    """
    Calculate resource utilization percentage.
    
    Args:
        busy_time: Time resource was busy
        total_time: Total simulation time
        
    Returns:
        Utilization as a percentage (0-100)
    """
    if total_time == 0:
        return 0.0
    return (busy_time / total_time) * 100
```

## Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for good test coverage

```bash
# Run tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_assembly.py
```

## Documentation

- Update README.md for user-facing changes
- Update CLAUDE.md for architecture changes
- Add docstrings to new functions and classes
- Include examples in docstrings when helpful

## Pull Request Process

1. **Update Documentation**: Ensure all documentation is updated
2. **Add Tests**: Include tests for new functionality
3. **Pass CI Checks**: Ensure all tests pass
4. **Clear Description**: Describe what changes you made and why
5. **Link Issues**: Reference any related issues

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
Describe the tests you ran

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] No new warnings
```

## Reporting Bugs

When reporting bugs, include:

- **Description**: Clear description of the bug
- **Steps to Reproduce**: Detailed steps to reproduce
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, package versions
- **Code Sample**: Minimal code that reproduces the issue

## Feature Requests

When suggesting features:

- **Use Case**: Describe the problem or use case
- **Proposed Solution**: How you envision the feature
- **Alternatives**: Other approaches you considered
- **Impact**: Who benefits and how

## Commit Messages

Write clear, concise commit messages:

- Use present tense ("Add feature" not "Added feature")
- First line: brief summary (50 chars or less)
- Add detailed description if needed
- Reference issues: "Fixes #123" or "Related to #456"

### Examples

```
Add password strength validation

Implement password validation with requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

Fixes #42
```

## Code Review

All submissions require review. Be patient and respectful during the review process.

Reviewers should:
- Provide constructive feedback
- Explain reasoning for requested changes
- Be timely in their reviews

Contributors should:
- Address feedback promptly
- Ask questions if unclear
- Be open to suggestions

## Areas for Contribution

Good areas to contribute:

- **Documentation**: Improve existing docs or add examples
- **Tests**: Increase test coverage
- **Bug Fixes**: Fix reported issues
- **Performance**: Optimize slow operations
- **Features**: Add new DES components or analysis tools
- **Examples**: Add simulation examples and tutorials

## Questions?

If you have questions:
- Check existing documentation
- Search closed issues
- Open a new issue with your question
- Tag it with "question" label

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
