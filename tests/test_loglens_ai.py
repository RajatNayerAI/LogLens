"""
Unit tests for loglens_ai.py
Tests cover log parsing, pattern matching, and core functionality
"""
import unittest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Import the module - adjust path as needed
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Code'))

from loglens_ai import (
    parse_line,
    suggest_hint,
    collect_lines,
    build_context,
    heuristic_summary,
    load_env_file,
    get_api_key,
    load_patterns,
    save_patterns,
    LEVEL_ORDER
)


class TestParseLine(unittest.TestCase):
    """Test log line parsing for different formats"""

    def test_parse_format1_timestamp_level_source_message(self):
        """Test Format 1: 2025-09-28 10:01:23 [LEVEL] [source] message"""
        line = "2025-09-28 10:01:23 [ERROR] [db-service] Connection refused"
        result = parse_line(line)
        
        self.assertEqual(result["timestamp"], "2025-09-28 10:01:23")
        self.assertEqual(result["level"], "ERROR")
        self.assertEqual(result["source"], "db-service")
        self.assertEqual(result["message"], "Connection refused")

    def test_parse_format1_with_milliseconds(self):
        """Test Format 1 with milliseconds"""
        line = "2025-09-28 10:01:23.456 [WARN] [app] Warning message"
        result = parse_line(line)
        
        self.assertEqual(result["timestamp"], "2025-09-28 10:01:23.456")
        self.assertEqual(result["level"], "WARN")
        self.assertEqual(result["source"], "app")
        self.assertEqual(result["message"], "Warning message")

    def test_parse_format2_level_timestamp_message(self):
        """Test Format 2: LEVEL 2025-09-28 10:01:23 message"""
        line = "ERROR 2025-09-28 10:01:23 Database connection timeout"
        result = parse_line(line)
        
        self.assertEqual(result["timestamp"], "2025-09-28 10:01:23")
        self.assertEqual(result["level"], "ERROR")
        self.assertEqual(result["message"], "Database connection timeout")

    def test_parse_format2_info_level(self):
        """Test Format 2 with INFO level"""
        line = "INFO 2025-09-28 10:01:23 Service started successfully"
        result = parse_line(line)
        
        self.assertEqual(result["level"], "INFO")
        self.assertEqual(result["message"], "Service started successfully")

    def test_parse_format3_java_style(self):
        """Test Format 3: [LEVEL] 2025-09-28 10:01:23 source - message"""
        line = "[ERROR] 2025-09-28 10:01:23 auth-service - Authentication failed"
        result = parse_line(line)
        
        self.assertEqual(result["timestamp"], "2025-09-28 10:01:23")
        self.assertEqual(result["level"], "ERROR")
        self.assertEqual(result["source"], "auth-service")
        self.assertEqual(result["message"], "Authentication failed")

    def test_parse_format4_android_logcat(self):
        """Test Format 4: Android logcat format"""
        line = "09-28 10:01:23.456 1234 5678 E MyApp: Fatal error occurred"
        result = parse_line(line)
        
        self.assertEqual(result["timestamp"], "09-28 10:01:23.456")
        self.assertEqual(result["level"], "ERROR")
        self.assertEqual(result["source"], "MyApp")
        self.assertEqual(result["message"], "Fatal error occurred")

    def test_parse_unknown_format(self):
        """Test unparseable line defaults to UNKNOWN"""
        line = "This is not a recognized log format"
        result = parse_line(line)
        
        self.assertEqual(result["level"], "UNKNOWN")
        self.assertEqual(result["message"], "This is not a recognized log format")
        self.assertEqual(result["timestamp"], "")
        self.assertEqual(result["source"], "")

    def test_parse_empty_line(self):
        """Test empty line handling"""
        line = ""
        result = parse_line(line)
        
        self.assertEqual(result["level"], "UNKNOWN")
        self.assertEqual(result["message"], "")

    def test_parse_level_normalization(self):
        """Test that levels are converted to uppercase"""
        line = "error 2025-09-28 10:01:23 Something broke"
        result = parse_line(line)
        
        self.assertEqual(result["level"], "ERROR")

    def test_parse_warning_aliases(self):
        """Test WARNING and WARN are handled"""
        line1 = "WARNING 2025-09-28 10:01:23 First warning"
        line2 = "WARN 2025-09-28 10:01:23 Second warning"
        
        result1 = parse_line(line1)
        result2 = parse_line(line2)
        
        self.assertEqual(result1["level"], "WARNING")
        self.assertEqual(result2["level"], "WARN")


class TestSuggestHint(unittest.TestCase):
    """Test hint suggestion for common error patterns"""

    def test_memory_issue_detection(self):
        """Test detection of OutOfMemory errors"""
        patterns = {}
        hint = suggest_hint("OutOfMemoryError: Java heap space", patterns)
        self.assertIn("memory", hint.lower())

    def test_null_pointer_detection(self):
        """Test detection of NullPointerException"""
        patterns = {}
        hint = suggest_hint("NullPointerException at line 42", patterns)
        self.assertIn("null", hint.lower())

    def test_connection_refused_detection(self):
        """Test detection of connection refused errors"""
        patterns = {}
        hint = suggest_hint("Connection refused to database", patterns)
        self.assertIn("unreachable", hint.lower())

    def test_timeout_detection(self):
        """Test detection of timeout errors"""
        patterns = {}
        hint = suggest_hint("Request timeout after 30s", patterns)
        self.assertIn("timeout", hint.lower())

    def test_pattern_matching(self):
        """Test custom pattern matching"""
        patterns = {
            "database error": "Check database connection",
            "API failure": "Verify API endpoint"
        }
        
        hint1 = suggest_hint("Critical database error occurred", patterns)
        hint2 = suggest_hint("API failure: 503 Service Unavailable", patterns)
        
        self.assertIn("database connection", hint1)
        self.assertIn("API endpoint", hint2)

    def test_empty_pattern_key_ignored(self):
        """Test that empty pattern keys are skipped"""
        patterns = {
            "": "This should not match",
            "real error": "This should match"
        }
        hint = suggest_hint("real error occurred", patterns)
        self.assertEqual(hint, "This should match")

    def test_unknown_issue_fallback(self):
        """Test fallback for unknown issues"""
        patterns = {}
        hint = suggest_hint("Something weird happened", patterns)
        self.assertIn("Unknown", hint)


class TestCollectLines(unittest.TestCase):
    """Test log collection and parsing from files"""

    def test_collect_lines_from_file(self):
        """Test collecting lines from a log file"""
        log_content = """INFO 2025-09-28 10:01:23 Service started
ERROR 2025-09-28 10:01:24 Connection failed
WARN 2025-09-28 10:01:25 High CPU usage"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_path = f.name
        
        try:
            entries, counts = collect_lines(temp_path)
            
            self.assertEqual(len(entries), 3)
            self.assertEqual(counts["INFO"], 1)
            self.assertEqual(counts["ERROR"], 1)
            self.assertEqual(counts["WARN"], 1)
            self.assertEqual(entries[0]["level"], "INFO")
            self.assertEqual(entries[1]["level"], "ERROR")
        finally:
            os.unlink(temp_path)

    def test_collect_lines_with_level_filter(self):
        """Test collecting lines filtered by level"""
        log_content = """INFO 2025-09-28 10:01:23 Service started
ERROR 2025-09-28 10:01:24 Connection failed
WARN 2025-09-28 10:01:25 High CPU usage
ERROR 2025-09-28 10:01:26 Another error"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_path = f.name
        
        try:
            entries, counts = collect_lines(temp_path, level="ERROR")
            
            self.assertEqual(len(entries), 2)
            self.assertTrue(all(e["level"] == "ERROR" for e in entries))
        finally:
            os.unlink(temp_path)

    def test_collect_lines_nonexistent_file(self):
        """Test handling of nonexistent file"""
        entries, counts = collect_lines("/nonexistent/path/to/file.log")
        
        self.assertEqual(entries, [])
        self.assertEqual(counts, {})

    def test_collect_lines_case_insensitive_level_filter(self):
        """Test that level filter is case-insensitive"""
        log_content = """INFO 2025-09-28 10:01:23 Service started
ERROR 2025-09-28 10:01:24 Connection failed"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_path = f.name
        
        try:
            entries1, _ = collect_lines(temp_path, level="error")
            entries2, _ = collect_lines(temp_path, level="ERROR")
            entries3, _ = collect_lines(temp_path, level="Error")
            
            self.assertEqual(len(entries1), 1)
            self.assertEqual(len(entries2), 1)
            self.assertEqual(len(entries3), 1)
        finally:
            os.unlink(temp_path)

    def test_collect_lines_with_encoding_errors(self):
        """Test handling of files with encoding errors"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.log') as f:
            # Write some binary data that's not valid UTF-8
            f.write(b'INFO 2025-09-28 10:01:23 Valid line\n')
            f.write(b'\xff\xfe Invalid UTF-8\n')
            f.write(b'ERROR 2025-09-28 10:01:24 Another valid line\n')
            f.flush()
            temp_path = f.name
        
        try:
            entries, counts = collect_lines(temp_path)
            # Should handle gracefully with errors="ignore"
            self.assertGreater(len(entries), 0)
        finally:
            os.unlink(temp_path)


class TestBuildContext(unittest.TestCase):
    """Test context building for AI prompts"""

    def test_build_context_basic(self):
        """Test building context from entries"""
        entries = [
            {"level": "ERROR", "timestamp": "2025-09-28 10:01:24", "message": "Error 1"},
            {"level": "WARN", "timestamp": "2025-09-28 10:01:25", "message": "Warning 1"},
            {"level": "INFO", "timestamp": "2025-09-28 10:01:23", "message": "Info 1"},
        ]
        counts = {"ERROR": 1, "WARN": 1, "INFO": 1}
        
        context = build_context(entries, counts, top_n=2)
        
        self.assertIn("stats", context)
        self.assertIn("top", context)
        self.assertEqual(context["stats"]["ERROR"], 1)
        self.assertEqual(context["stats"]["WARN"], 1)
        self.assertEqual(len(context["top"]), 2)

    def test_build_context_top_n_limit(self):
        """Test that top_n parameter limits results"""
        entries = [
            {"level": "ERROR", "timestamp": "2025-09-28 10:01:24", "message": f"Error {i}"}
            for i in range(20)
        ]
        counts = {"ERROR": 20}
        
        context = build_context(entries, counts, top_n=5)
        
        self.assertEqual(len(context["top"]), 5)

    def test_build_context_empty_entries(self):
        """Test building context with empty entries"""
        context = build_context([], {}, top_n=10)
        
        self.assertEqual(len(context["top"]), 0)
        self.assertEqual(context["stats"]["INFO"], 0)


class TestHeuristicSummary(unittest.TestCase):
    """Test heuristic summary generation"""

    def test_heuristic_summary_with_errors(self):
        """Test summary generation with errors"""
        entries = [
            {"level": "ERROR", "message": "Error 1"},
            {"level": "WARN", "message": "Warning 1"},
        ]
        counts = {"ERROR": 2, "WARN": 1, "INFO": 5}
        
        summary = heuristic_summary(entries, counts)
        
        self.assertIn("2 error(s)", summary)
        self.assertIn("1 warning(s)", summary)
        self.assertIn("5 info messages", summary)

    def test_heuristic_summary_empty(self):
        """Test summary with no entries"""
        summary = heuristic_summary([], {})
        
        self.assertIn("No significant events", summary)

    def test_heuristic_summary_includes_top_messages(self):
        """Test that summary includes top messages"""
        entries = [
            {"level": "ERROR", "message": "Database connection failed"},
            {"level": "WARN", "message": "High memory usage"},
        ]
        counts = {"ERROR": 1, "WARN": 1}
        
        summary = heuristic_summary(entries, counts)
        
        self.assertIn("Database connection failed", summary)
        self.assertIn("High memory usage", summary)


class TestEnvFileHandling(unittest.TestCase):
    """Test environment file parsing"""

    def test_load_env_file_basic(self):
        """Test basic .env file loading"""
        env_content = """
OPENAI_API_KEY=sk-test123456
DEBUG=true
LOG_LEVEL=INFO
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
            f.write(env_content)
            f.flush()
            temp_path = Path(f.name)
        
        try:
            data = load_env_file(temp_path)
            
            self.assertEqual(data["OPENAI_API_KEY"], "sk-test123456")
            self.assertEqual(data["DEBUG"], "true")
            self.assertEqual(data["LOG_LEVEL"], "INFO")
        finally:
            temp_path.unlink()

    def test_load_env_file_with_comments(self):
        """Test .env file with comments"""
        env_content = """
# This is a comment
OPENAI_API_KEY=sk-test123456
# Another comment
DEBUG=true
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
            f.write(env_content)
            f.flush()
            temp_path = Path(f.name)
        
        try:
            data = load_env_file(temp_path)
            
            self.assertEqual(len(data), 2)
            self.assertNotIn("This is a comment", str(data))
        finally:
            temp_path.unlink()

    def test_load_env_file_with_quotes(self):
        """Test .env file with quoted values"""
        env_content = """
KEY1="value1"
KEY2='value2'
KEY3=value3
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
            f.write(env_content)
            f.flush()
            temp_path = Path(f.name)
        
        try:
            data = load_env_file(temp_path)
            
            self.assertEqual(data["KEY1"], "value1")
            self.assertEqual(data["KEY2"], "value2")
            self.assertEqual(data["KEY3"], "value3")
        finally:
            temp_path.unlink()

    def test_load_env_file_nonexistent(self):
        """Test loading nonexistent .env file"""
        data = load_env_file(Path("/nonexistent/.env"))
        
        self.assertEqual(data, {})


class TestPatternHandling(unittest.TestCase):
    """Test pattern file saving and loading"""

    def test_save_and_load_patterns(self):
        """Test saving and loading patterns"""
        test_patterns = {
            "OutOfMemory": "Possible memory issue.",
            "Connection refused": "Service unreachable/network.",
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pattern_file = os.path.join(tmpdir, "patterns.json")
            
            # Patch the PATTERN_FILE path
            with patch('loglens_ai.PATTERN_FILE', pattern_file):
                save_patterns(test_patterns)
                loaded = load_patterns()
            
            self.assertEqual(loaded["OutOfMemory"], "Possible memory issue.")
            self.assertEqual(loaded["Connection refused"], "Service unreachable/network.")

    def test_load_patterns_invalid_json(self):
        """Test handling of invalid JSON in patterns file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pattern_file = os.path.join(tmpdir, "patterns.json")
            
            # Write invalid JSON
            with open(pattern_file, 'w') as f:
                f.write("{invalid json")
            
            with patch('loglens_ai.PATTERN_FILE', pattern_file):
                patterns = load_patterns()
            
            # Should return empty dict on error
            self.assertEqual(patterns, {})


class TestInputValidation(unittest.TestCase):
    """Test input validation and edge cases"""

    def test_collect_lines_case_insensitive_level(self):
        """Test that level filtering is case-insensitive"""
        log_content = "ERROR 2025-09-28 10:01:23 Error message"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_path = f.name
        
        try:
            entries_lower, _ = collect_lines(temp_path, level="error")
            entries_upper, _ = collect_lines(temp_path, level="ERROR")
            entries_mixed, _ = collect_lines(temp_path, level="ErRoR")
            
            self.assertEqual(len(entries_lower), 1)
            self.assertEqual(len(entries_upper), 1)
            self.assertEqual(len(entries_mixed), 1)
        finally:
            os.unlink(temp_path)

    def test_parse_line_with_special_characters(self):
        """Test parsing lines with special characters"""
        line = '2025-09-28 10:01:23 [ERROR] [app] Message with "quotes" and \\n escapes'
        result = parse_line(line)
        
        self.assertEqual(result["level"], "ERROR")
        self.assertIn("quotes", result["message"])

    def test_collect_lines_empty_file(self):
        """Test collecting lines from empty file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.flush()
            temp_path = f.name
        
        try:
            entries, counts = collect_lines(temp_path)
            
            self.assertEqual(len(entries), 0)
            self.assertEqual(len(counts), 0)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
