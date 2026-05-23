"""
Unit tests for loglens.py (core log analysis without AI)
"""
import unittest
import os
import tempfile
import csv
import json

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Code'))

from loglens import (
    parse_line,
    suggest_hint,
    analyse_file,
    tail_file,
    load_patterns,
    save_patterns,
    LEVEL_ORDER
)


class TestParseLineCore(unittest.TestCase):
    """Test core log parsing functionality"""

    def test_parse_vs_code_format(self):
        """Test VS Code style: timestamp [level] [source] message"""
        line = "2025-09-28 10:01:23 [ERROR] [database] Connection timeout"
        result = parse_line(line)
        
        self.assertEqual(result["timestamp"], "2025-09-28 10:01:23")
        self.assertEqual(result["level"], "ERROR")
        self.assertEqual(result["source"], "database")
        self.assertEqual(result["message"], "Connection timeout")

    def test_parse_vs_code_format_with_milliseconds(self):
        """Test VS Code format with milliseconds"""
        line = "2025-09-28 10:01:23.789 [WARN] [auth] Invalid credentials"
        result = parse_line(line)
        
        self.assertEqual(result["timestamp"], "2025-09-28 10:01:23.789")
        self.assertEqual(result["level"], "WARN")

    def test_parse_java_server_format(self):
        """Test Java server log: [LEVEL] TIMESTAMP SOURCE - Message"""
        line = "[ERROR] 2025-09-28 10:01:23 api-gateway - 503 Service Unavailable"
        result = parse_line(line)
        
        self.assertEqual(result["timestamp"], "2025-09-28 10:01:23")
        self.assertEqual(result["level"], "ERROR")
        self.assertEqual(result["source"], "api-gateway")
        self.assertEqual(result["message"], "503 Service Unavailable")

    def test_parse_unknown_format_defaults_correctly(self):
        """Test that unknown formats default properly"""
        line = "Random log line without structure"
        result = parse_line(line)
        
        self.assertEqual(result["level"], "UNKNOWN")
        self.assertEqual(result["message"], "Random log line without structure")
        self.assertEqual(result["timestamp"], "")
        self.assertEqual(result["source"], "")

    def test_parse_level_case_conversion(self):
        """Test that levels are uppercase"""
        line = "2025-09-28 10:01:23 [error] [service] Message"
        result = parse_line(line)
        
        self.assertEqual(result["level"], "ERROR")


class TestSuggestHintCore(unittest.TestCase):
    """Test hint suggestion in core module"""

    def test_suggest_hint_with_patterns(self):
        """Test suggesting hints from loaded patterns"""
        patterns = {
            "timeout": "Network or service latency issue",
            "OutOfMemory": "Heap memory exhausted"
        }
        
        hint1 = suggest_hint("Request timeout", patterns)
        hint2 = suggest_hint("OutOfMemory in JVM", patterns)
        
        self.assertEqual(hint1, "Network or service latency issue")
        self.assertEqual(hint2, "Heap memory exhausted")

    def test_suggest_hint_unknown_default(self):
        """Test default hint for unknown patterns"""
        patterns = {}
        hint = suggest_hint("Unknown error occurred", patterns)
        
        self.assertEqual(hint, "Unknown issue, needs review")


class TestAnalyseFile(unittest.TestCase):
    """Test file analysis functionality"""

    def test_analyse_file_basic(self):
        """Test basic file analysis"""
        log_content = """2025-09-28 10:01:23 [INFO] [app] Service started
2025-09-28 10:01:24 [ERROR] [db] Connection refused
2025-09-28 10:01:25 [WARN] [app] High CPU usage"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_path = f.name
        
        try:
            # Capture output
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                analyse_file(temp_path)
            
            output = f.getvalue()
            self.assertIn("INFO=1", output)
            self.assertIn("ERROR=1", output)
            self.assertIn("WARN=1", output)
        finally:
            os.unlink(temp_path)

    def test_analyse_file_nonexistent(self):
        """Test analysis on nonexistent file"""
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            analyse_file("/nonexistent/file.log")
        
        output = f.getvalue()
        self.assertIn("File not found", output)

    def test_analyse_file_with_export_json(self):
        """Test exporting analysis results to JSON"""
        log_content = """2025-09-28 10:01:23 [INFO] [app] Service started
2025-09-28 10:01:24 [ERROR] [db] Connection refused"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            log_path = f.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            export_path = f.name
        
        try:
            import io
            from contextlib import redirect_stdout
            
            f_out = io.StringIO()
            with redirect_stdout(f_out):
                analyse_file(log_path, export=export_path)
            
            # Verify JSON was created
            self.assertTrue(os.path.exists(export_path))
            
            with open(export_path, 'r') as f:
                data = json.load(f)
                self.assertIsInstance(data, list)
                self.assertGreater(len(data), 0)
        finally:
            os.unlink(log_path)
            if os.path.exists(export_path):
                os.unlink(export_path)

    def test_analyse_file_with_export_csv(self):
        """Test exporting analysis results to CSV"""
        log_content = """2025-09-28 10:01:23 [INFO] [app] Service started
2025-09-28 10:01:24 [ERROR] [db] Connection refused"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            log_path = f.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as f:
            export_path = f.name
        
        try:
            import io
            from contextlib import redirect_stdout
            
            f_out = io.StringIO()
            with redirect_stdout(f_out):
                analyse_file(log_path, export=export_path)
            
            # Verify CSV was created
            self.assertTrue(os.path.exists(export_path))
            
            with open(export_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertGreater(len(rows), 0)
                self.assertIn('line', reader.fieldnames)
                self.assertIn('level', reader.fieldnames)
        finally:
            os.unlink(log_path)
            if os.path.exists(export_path):
                os.unlink(export_path)

    def test_analyse_file_with_level_filter(self):
        """Test analysis with level filtering"""
        log_content = """2025-09-28 10:01:23 [INFO] [app] Service started
2025-09-28 10:01:24 [ERROR] [db] Connection refused
2025-09-28 10:01:25 [ERROR] [db] Another error
2025-09-28 10:01:26 [WARN] [app] Warning message"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_path = f.name
        
        try:
            import io
            from contextlib import redirect_stdout
            
            f_out = io.StringIO()
            with redirect_stdout(f_out):
                analyse_file(temp_path, level="ERROR")
            
            output = f_out.getvalue()
            # Should only show ERROR level entries in top issues
            self.assertIn("ERROR", output)
        finally:
            os.unlink(temp_path)

    def test_analyse_file_top_n_limit(self):
        """Test that -n parameter limits results"""
        log_content = "\n".join([
            f"2025-09-28 10:01:{i:02d} [ERROR] [app] Error {i}"
            for i in range(20)
        ])
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_path = f.name
        
        try:
            import io
            from contextlib import redirect_stdout
            
            f_out = io.StringIO()
            with redirect_stdout(f_out):
                analyse_file(temp_path, n=5)
            
            output = f_out.getvalue()
            # Count ERROR lines in output (should be limited to top 5)
            error_count = output.count("ERROR")
            # The stats line has one ERROR, plus top 5 errors = 6
            self.assertLessEqual(error_count, 7)  # Some buffer for stats
        finally:
            os.unlink(temp_path)


class TestTailFile(unittest.TestCase):
    """Test log file tailing functionality"""

    def test_tail_file_basic(self):
        """Test tailing basic log file"""
        log_content = "\n".join([f"Line {i}" for i in range(20)])
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_path = f.name
        
        try:
            lines = tail_file(temp_path, lines=5)
            
            self.assertEqual(len(lines), 5)
            self.assertEqual(lines[-1], "Line 19")
            self.assertEqual(lines[-2], "Line 18")
        finally:
            os.unlink(temp_path)

    def test_tail_file_less_lines_than_requested(self):
        """Test tailing when file has fewer lines than requested"""
        log_content = "\n".join([f"Line {i}" for i in range(3)])
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_path = f.name
        
        try:
            lines = tail_file(temp_path, lines=10)
            
            self.assertEqual(len(lines), 3)
        finally:
            os.unlink(temp_path)

    def test_tail_file_empty_file(self):
        """Test tailing empty file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.flush()
            temp_path = f.name
        
        try:
            lines = tail_file(temp_path, lines=10)
            
            self.assertEqual(len(lines), 0)
        finally:
            os.unlink(temp_path)

    def test_tail_file_large_file(self):
        """Test tailing large file efficiently"""
        # Create a file with 10000 lines
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            for i in range(10000):
                f.write(f"Line {i}\n")
            f.flush()
            temp_path = f.name
        
        try:
            lines = tail_file(temp_path, lines=100)
            
            self.assertEqual(len(lines), 100)
            self.assertEqual(lines[-1], "Line 9999")
            self.assertEqual(lines[0], "Line 9900")
        finally:
            os.unlink(temp_path)


class TestPatternHandlingCore(unittest.TestCase):
    """Test pattern file operations in core module"""

    def test_patterns_file_creation(self):
        """Test that patterns file is created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                patterns = {"test": "hint"}
                save_patterns(patterns)
                
                self.assertTrue(os.path.exists("patterns.json"))
                
                loaded = load_patterns()
                self.assertEqual(loaded["test"], "hint")
            finally:
                os.chdir(old_cwd)

    def test_patterns_persistence(self):
        """Test that patterns persist across saves"""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                patterns1 = {"error1": "hint1"}
                save_patterns(patterns1)
                
                patterns2 = {"error2": "hint2"}
                patterns2.update(patterns1)
                save_patterns(patterns2)
                
                loaded = load_patterns()
                self.assertEqual(len(loaded), 2)
                self.assertIn("error1", loaded)
                self.assertIn("error2", loaded)
            finally:
                os.chdir(old_cwd)


class TestLevelOrdering(unittest.TestCase):
    """Test log level ordering constants"""

    def test_level_order_hierarchy(self):
        """Test that levels are ordered by severity"""
        self.assertGreater(LEVEL_ORDER["ERROR"], LEVEL_ORDER["WARN"])
        self.assertGreater(LEVEL_ORDER["WARN"], LEVEL_ORDER["INFO"])
        self.assertGreater(LEVEL_ORDER["INFO"], LEVEL_ORDER["UNKNOWN"])

    def test_warning_aliases_same_level(self):
        """Test that WARN and WARNING have same priority"""
        self.assertEqual(LEVEL_ORDER["WARN"], LEVEL_ORDER["WARNING"])


if __name__ == '__main__':
    unittest.main()
