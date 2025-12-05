# Test Suite Documentation

## Overview

This directory contains comprehensive unit and system tests for the AI Research Agent application.

## Test Structure

### Unit Tests

- `test_llm_client.py`: Tests for OpenRouter API client
- `test_query_refiner.py`: Tests for topic refinement functionality
- `test_outline_builder.py`: Tests for outline generation
- `test_section_researcher.py`: Tests for section research and citation
- `test_html_writer.py`: Tests for HTML generation
- `test_pipeline.py`: Tests for pipeline orchestration
- `test_app.py`: Tests for Flask web application
- `test_storage.py`: Tests for storage utilities

### System/Integration Tests

- `test_system.py`: End-to-end integration tests

## Running Tests

### Using pytest directly

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_llm_client.py

# Run specific test
pytest tests/test_llm_client.py::TestLLMClient::test_call_llm_success
```

### Using the test runner script

```bash
# Run all tests
python run_tests.py

# Run with coverage report
python run_tests.py --cov
```

### Test Markers

Tests can be run by marker:

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# System tests only
pytest -m system
```

## Test Coverage

The test suite aims for comprehensive coverage of:

1. **LLM Client**: API calls, error handling, retries
2. **Query Refiner**: Topic refinement, query generation, error handling
3. **Outline Builder**: Section generation, priority sorting, fallbacks
4. **Section Researcher**: Section research, citation handling, source management
5. **HTML Writer**: HTML generation, escaping, formatting
6. **Pipeline**: End-to-end report generation, source deduplication, citation normalization
7. **Web App**: Routes, error handling, history management
8. **Storage**: File operations, session management

## Mocking Strategy

Tests use extensive mocking to:
- Avoid actual API calls to OpenRouter
- Isolate unit functionality
- Test error conditions
- Speed up test execution

Key mocks:
- `call_llm`: Mocked in all tests that use LLM
- `requests.post`: Mocked in LLM client tests
- File system operations: Use temporary directories

## Test Fixtures

Tests use temporary directories for:
- History storage (`history/`)
- Session storage (`storage/sessions/`)

All temporary files are cleaned up after tests.

## Writing New Tests

When adding new functionality:

1. Add unit tests for the new module
2. Update integration tests if the pipeline changes
3. Add system tests for new web endpoints
4. Ensure error cases are covered
5. Mock external dependencies

## Continuous Integration

Tests should be run:
- Before committing code
- In CI/CD pipeline
- After major refactoring

## Known Limitations

- Tests don't verify actual LLM responses (mocked)
- Some edge cases in error handling may need additional coverage
- Performance tests not included (focus on functionality)

