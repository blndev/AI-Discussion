# AI Discussion Tests

This directory contains unit tests for the AI Discussion system.

## Test Coverage

### Actor Tests (`test_actor.py`)
- Actor initialization
- Context management
- Prompt generation
- Response handling
- Error cases

### Moderator Tests (`test_moderator.py`)
- ModeratorTools functionality
- Actor selection logic
- Prompt generation for different actors
- Tool call handling
- Error handling

## Running Tests

You can run all tests using Python's unittest framework:

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests/test_actor.py
python -m unittest tests/test_moderator.py

# Run specific test case
python -m unittest tests.test_actor.TestActor
python -m unittest tests.test_moderator.TestModerator
```

## Test Structure

Each test file follows this structure:
1. Test fixtures in `setUp()`
2. Mocked dependencies (e.g., LLM responses)
3. Individual test cases for specific functionality
4. Error case handling

## Adding New Tests

When adding new tests:
1. Follow the existing naming convention: `test_*.py`
2. Use descriptive test method names
3. Add proper docstrings explaining the test purpose
4. Mock external dependencies (especially LLM calls)
5. Test both success and error cases
