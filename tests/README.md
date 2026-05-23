# Testing Guide for LogLens

## Overview

This directory contains comprehensive unit tests for the LogLens project, covering both the core module (`loglens.py`) and the AI-enhanced module (`loglens_ai.py`).

## Test Files

- **`test_loglens_ai.py`** (18+ tests)
  - Tests for log parsing (4 formats + edge cases)
  - Hint suggestion and pattern matching
  - File collection and context building
  - Environment file handling
  - Pattern file persistence

- **`test_loglens.py`** (15+ tests)
  - Core log analysis functionality
  - Export to JSON/CSV
  - Log file tailing
  - Level filtering and sorting
  - Pattern management

## Setup

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

This installs:
- `pytest` - Test runner
- `pytest-cov` - Coverage plugin
- `coverage` - Code coverage analysis
- `openai` - For AI module tests

## Running Tests

### Run All Tests

```bash
pytest
# or
python -m pytest
```

### Run Specific Test File

```bash
pytest tests/test_loglens_ai.py
pytest tests/test_loglens.py
```

### Run Specific Test Class

```bash
pytest tests/test_loglens_ai.py::TestParseLine
pytest tests/test_loglens_ai.py::TestSuggestHint
```

### Run Specific Test Method

```bash
pytest tests/test_loglens_ai.py::TestParseLine::test_parse_format1_timestamp_level_source_message
```

### Verbose Output

```bash
pytest -v
```

### Show Print Statements

```bash
pytest -s
```

## Coverage Analysis

### Generate Coverage Report

```bash
pytest --cov=Code tests/
```

### Generate HTML Coverage Report

```bash
pytest --cov=Code --cov-report=html tests/
# Open htmlcov/index.html in browser
```

### Show Coverage on Specific Module

```bash
pytest --cov=Code.loglens_ai tests/test_loglens_ai.py
```

## Test Categories

### 1. Log Parsing Tests (`TestParseLine`)
Tests 4 different log format parsers:
- Format 1: `2025-09-28 10:01:23 [LEVEL] [source] message`
- Format 2: `LEVEL 2025-09-28 10:01:23 message`
- Format 3: `[LEVEL] 2025-09-28 10:01:23 source - message` (Java)
- Format 4: Android logcat format

**Coverage:**
- Millisecond precision timestamps
- Level normalization to uppercase
- Edge cases (empty lines, special characters)
- Unknown format fallback

### 2. Hint Suggestion Tests (`TestSuggestHint`)
Tests pattern-based error hints and heuristics:
- Custom pattern matching
- Built-in heuristics (OOM, NPE, connection errors)
- Empty pattern handling
- Unknown issue fallback

**Coverage:**
- Memory error detection
- Network timeout detection
- Null reference detection
- Custom pattern database

### 3. File Collection Tests (`TestCollectLines`)
Tests log file reading and filtering:
- Multi-level log collection
- Level-based filtering (case-insensitive)
- Encoding error handling
- Large file support

**Coverage:**
- Multiple log levels in single file
- Filter by level (ERROR, WARN, INFO)
- Graceful UTF-8 error handling
- Statistics aggregation

### 4. Export Tests (`TestAnalyseFile`)
Tests analysis output and exports:
- JSON export
- CSV export
- Top N limiting
- Statistics generation

**Coverage:**
- Export to JSON format
- Export to CSV with headers
- Summary statistics
- Nonexistent file handling

### 5. Tail Tests (`TestTailFile`)
Tests efficient log tailing:
- Last N lines extraction
- Large file support (10K+ lines)
- Empty file handling
- Buffer efficiency

**Coverage:**
- Efficient tail implementation
- Handles files larger than memory buffer
- Works with files smaller than requested tail size

### 6. Environment & Config Tests
Tests configuration file handling:
- `.env` file parsing
- Comment and quote handling
- Quoted and unquoted values
- Fallback behavior

**Coverage:**
- Multi-line env files
- Comments and blank lines
- Single and double quoted values
- Missing files

### 7. Pattern Persistence Tests
Tests pattern file management:
- Save patterns to JSON
- Load patterns from JSON
- Invalid JSON handling
- Pattern updates

**Coverage:**
- New pattern creation
- Pattern updates across saves
- Graceful error handling
- File encoding

## Example Test Run

```bash
$ pytest -v tests/

tests/test_loglens_ai.py::TestParseLine::test_parse_format1_timestamp_level_source_message PASSED
tests/test_loglens_ai.py::TestParseLine::test_parse_format2_level_timestamp_message PASSED
tests/test_loglens_ai.py::TestSuggestHint::test_memory_issue_detection PASSED
tests/test_loglens_ai.py::TestCollectLines::test_collect_lines_from_file PASSED
tests/test_loglens_ai.py::TestCollectLines::test_collect_lines_with_level_filter PASSED
...

========================= 33 passed in 0.42s =========================
```

## Continuous Integration

To run tests in CI/CD pipeline:

```bash
# Install
pip install -r requirements-test.txt

# Run tests with coverage
pytest --cov=Code --cov-report=term-missing tests/

# Generate JUnit XML for CI systems
pytest --junitxml=test-results.xml tests/
```

## Writing New Tests

### Test Structure

```python
class TestFeature(unittest.TestCase):
    """Description of what you're testing"""
    
    def test_specific_case(self):
        """Specific test case description"""
        # Arrange
        input_data = "test input"
        
        # Act
        result = function_to_test(input_data)
        
        # Assert
        self.assertEqual(result, expected_value)
```

### Common Assertions

```python
self.assertEqual(a, b)           # a == b
self.assertNotEqual(a, b)        # a != b
self.assertTrue(x)               # bool(x) is True
self.assertFalse(x)              # bool(x) is False
self.assertIn(a, b)              # a in b
self.assertNotIn(a, b)           # a not in b
self.assertIsNone(x)             # x is None
self.assertIsNotNone(x)          # x is not None
self.assertGreater(a, b)         # a > b
self.assertLess(a, b)            # a < b
self.assertRaises(Exception, fn) # fn() raises Exception
```

### Mocking External Calls

```python
from unittest.mock import patch, MagicMock

@patch('module.external_function')
def test_with_mock(self, mock_func):
    mock_func.return_value = "mocked"
    result = function_that_calls_external()
    self.assertEqual(result, "mocked")
```

## Troubleshooting

### Import Errors

If you get `ImportError` when running tests:

```bash
# Ensure the Code directory is in Python path
export PYTHONPATH="${PYTHONPATH}:./Code"
pytest
```

### Module Not Found

```bash
# Make sure you're in the repository root
cd /path/to/LogLens
pytest
```

### Test Failures

Run with verbose and print output:

```bash
pytest -vvs tests/test_loglens_ai.py::TestParseLine::test_parse_format1_timestamp_level_source_message
```

## Best Practices

1. **Use temporary files** - Use `tempfile` module for file operations
2. **Clean up resources** - Always delete temporary files in teardown
3. **Test edge cases** - Empty inputs, large inputs, malformed data
4. **Mock external dependencies** - Use `unittest.mock` for API calls
5. **Isolate tests** - Each test should be independent
6. **Clear descriptions** - Use descriptive test names and docstrings
7. **Test one thing** - Each test should verify one behavior

## Target Coverage

- **Minimum:** 80% code coverage
- **Target:** 90% code coverage
- **Critical paths:** 100% coverage (parsing, error handling)

## References

- [pytest Documentation](https://docs.pytest.org/)
- [unittest Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [pytest Coverage Plugin](https://pytest-cov.readthedocs.io/)
