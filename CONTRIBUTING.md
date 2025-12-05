# Contributing to AI Research Agent

Thank you for your interest in contributing to AI Research Agent! This document provides guidelines and instructions for contributing.

## 🤝 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## 🚀 Getting Started

1. **Fork the repository**
2. **Clone your fork**: `git clone https://github.com/your-username/research_agent.git`
3. **Create a branch**: `git checkout -b feature/your-feature-name`
4. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## 📝 Development Workflow

### Making Changes

1. **Create a feature branch** from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards

3. **Write tests** for new functionality
   ```bash
   pytest tests/test_your_module.py
   ```

4. **Run all tests** to ensure nothing breaks
   ```bash
   pytest
   ```

5. **Check code style** (if using a linter)
   ```bash
   # Example with flake8
   flake8 .
   ```

6. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: Description of your changes"
   ```

7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Open a Pull Request** on GitHub

## 📋 Coding Standards

### Python Style

- Follow **PEP 8** style guidelines
- Use **type hints** where appropriate
- Write **docstrings** for all functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

### Code Structure

- Keep modules focused on a single responsibility
- Add error handling for external API calls
- Include logging for important operations
- Write tests for new features

### Example

```python
from typing import Dict, Any, List

def process_data(input_data: List[str]) -> Dict[str, Any]:
    """
    Process input data and return structured output.
    
    Args:
        input_data: List of input strings to process
        
    Returns:
        Dictionary containing processed data
        
    Raises:
        ValueError: If input_data is empty
    """
    if not input_data:
        raise ValueError("input_data cannot be empty")
    
    # Processing logic here
    return {"processed": True}
```

## 🧪 Testing Guidelines

### Writing Tests

- Write tests for all new features
- Aim for high test coverage
- Test both success and error cases
- Use descriptive test names

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_pipeline.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run with verbose output
pytest -v
```

### Test Structure

```python
import pytest
from your_module import your_function

class TestYourFunction:
    def test_success_case(self):
        """Test successful execution."""
        result = your_function("input")
        assert result == "expected"
    
    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            your_function("")
```

## 📚 Documentation

### Code Documentation

- Add docstrings to all functions and classes
- Include parameter descriptions and return types
- Document exceptions that may be raised

### README Updates

- Update README.md if you add new features
- Update installation instructions if dependencies change
- Add examples for new functionality

## 🔍 Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Ensure all tests pass**
4. **Update CHANGELOG.md** (if it exists)
5. **Write a clear PR description**:
   - What changes were made
   - Why the changes were made
   - How to test the changes

### PR Title Format

- `Add: Feature description`
- `Fix: Bug description`
- `Update: What was updated`
- `Refactor: What was refactored`

## 🐛 Reporting Bugs

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:

- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Screenshots if applicable

## 💡 Suggesting Features

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md) and include:

- Clear description of the feature
- Motivation and use cases
- Proposed implementation approach
- Examples or mockups if applicable

## ❓ Questions?

- Open a [Discussion](https://github.com/sgogi1/research_agent/discussions)
- Check existing [Issues](https://github.com/sgogi1/research_agent/issues)
- Review the [README](README.md)

## 🙏 Thank You!

Your contributions make this project better for everyone. Thank you for taking the time to contribute!

