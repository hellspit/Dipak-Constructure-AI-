# Test Suite

This directory contains the test suite for the Email Assistant API.

## Running Tests

### Install test dependencies
```bash
pip install -r requirements.txt
```

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_auth.py
```

### Run specific test
```bash
pytest tests/test_auth.py::TestAuthEndpoints::test_google_auth_initiate
```

### Run with verbose output
```bash
pytest -v
```

## Test Structure

- `conftest.py` - Shared fixtures and test configuration
- `test_models.py` - Tests for JSON storage models
- `test_auth.py` - Tests for authentication endpoints
- `test_email.py` - Tests for email operations
- `test_chatbot.py` - Tests for chatbot endpoints

## Test Coverage

The test suite covers:
- ✅ JSON session storage (create, read, update, delete)
- ✅ Google OAuth authentication flow
- ✅ Session management
- ✅ Email listing and operations
- ✅ AI reply generation
- ✅ Chatbot message processing
- ✅ Error handling

## Notes

- Tests use temporary files for JSON storage to avoid affecting production data
- All external API calls (Google, Groq) are mocked
- Tests are isolated and can run in any order

