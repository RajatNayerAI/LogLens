"""
Integration tests using sample log files from Logs- Sample Data folder
Tests the actual log analysis on real-world sample data
"""
import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Code'))

from loglens_ai import (
    parse_line,
    suggest_hint,
    collect_lines,
    build_context,
    heuristic_summary,
    LEVEL_ORDER
)

# Sample log file paths
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), '..', 'Logs- Sample Data')

SAMPLE_FILES = {
    'python_dev': os.path.join(SAMPLE_DIR, 'Python-dev.log'),
    'android': os.path.join(SAMPLE_DIR, 'android.log'),
    'android2': os.path.join(SAMPLE_DIR, 'android2.log'),
    'apps_log': os.path.join(SAMPLE_DIR, 'apps_log.log'),
    'dev_server': os.path.join(SAMPLE_DIR, 'dev_server.log'),
    'java_server': os.path.join(SAMPLE_DIR, 'java_server.log'),
    'prod_server': os.path.join(SAMPLE_DIR, 'prod_server.log'),
    'vscode': os.path.join(SAMPLE_DIR, 'vscode.log'),
    'vscode2': os.path.join(SAMPLE_DIR, 'vscode2.log'),
    'vscode3': os.path.join(SAMPLE_DIR, 'vscode3.log'),
}


class TestPythonDevLog(unittest.TestCase):
    """Test parsing Python dev environment logs"""

    def setUp(self):
        self.log_path = SAMPLE_FILES['python_dev']
        self.assertTrue(os.path.exists(self.log_path), f"Sample file not found: {self.log_path}")

    def test_collect_python_dev_logs(self):
        """Test collecting entries from Python dev log"""
        entries, counts = collect_lines(self.log_path)
        
        self.assertGreater(len(entries), 0, "Should have parsed entries")
        self.assertEqual(counts.get("INFO", 0), 2)
        self.assertEqual(counts.get("WARN", 0), 1)
        self.assertEqual(counts.get("ERROR", 0), 2)

    def test_python_dev_error_detection(self):
        """Test that errors are properly detected"""
        entries, counts = collect_lines(self.log_path, level="ERROR")
        
        self.assertEqual(len(entries), 2)
        self.assertTrue(any("Connection refused" in e["message"] for e in entries))
        self.assertTrue(any("TypeError" in e["message"] for e in entries))

    def test_python_dev_summary(self):
        """Test generating summary from Python dev logs"""
        entries, counts = collect_lines(self.log_path)
        summary = heuristic_summary(entries, counts)
        
        self.assertIn("2 error(s)", summary)
        self.assertIn("1 warning(s)", summary)
        self.assertGreater(len(summary), 0)

    def test_python_dev_context(self):
        """Test building context for AI analysis"""
        entries, counts = collect_lines(self.log_path)
        context = build_context(entries, counts, top_n=5)
        
        self.assertIn("stats", context)
        self.assertIn("top", context)
        self.assertEqual(context["stats"]["ERROR"], 2)


class TestAndroidLog(unittest.TestCase):
    """Test parsing Android logcat files"""

    def setUp(self):
        self.log_path = SAMPLE_FILES['android']
        self.assertTrue(os.path.exists(self.log_path), f"Sample file not found: {self.log_path}")

    def test_collect_android_logs(self):
        """Test collecting Android logcat entries"""
        entries, counts = collect_lines(self.log_path)
        
        self.assertGreater(len(entries), 0, "Should have parsed entries")
        # Android format should be detected
        self.assertTrue(any(e.get("source") for e in entries if e.get("source")))

    def test_android_error_detection(self):
        """Test error detection in Android logs"""
        entries, counts = collect_lines(self.log_path, level="ERROR")
        
        self.assertGreater(len(entries), 0)
        error_entries = [e for e in entries if e["level"] == "ERROR"]
        self.assertGreater(len(error_entries), 0)

    def test_android_large_file(self):
        """Test parsing larger Android log file"""
        log_path = SAMPLE_FILES['android2']
        if os.path.exists(log_path):
            entries, counts = collect_lines(log_path)
            
            self.assertGreater(len(entries), 0)
            # Should have multiple log levels
            self.assertGreater(len(counts), 0)


class TestDevServerLog(unittest.TestCase):
    """Test parsing development server logs"""

    def setUp(self):
        self.log_path = SAMPLE_FILES['dev_server']
        self.assertTrue(os.path.exists(self.log_path), f"Sample file not found: {self.log_path}")

    def test_collect_dev_server_logs(self):
        """Test collecting dev server log entries"""
        entries, counts = collect_lines(self.log_path)
        
        self.assertEqual(counts.get("INFO", 0), 5)
        self.assertEqual(counts.get("WARN", 0), 2)
        self.assertEqual(counts.get("ERROR", 0), 2)

    def test_dev_server_null_pointer_detection(self):
        """Test detection of NullPointerException"""
        entries, counts = collect_lines(self.log_path)
        
        error_entries = [e for e in entries if "NullPointerException" in e["message"]]
        self.assertEqual(len(error_entries), 1)
        
        hint = suggest_hint(error_entries[0]["message"], {})
        self.assertIn("null", hint.lower())

    def test_dev_server_filtering(self):
        """Test filtering by log level"""
        errors, _ = collect_lines(self.log_path, level="ERROR")
        warns, _ = collect_lines(self.log_path, level="WARN")
        
        self.assertEqual(len(errors), 2)
        self.assertEqual(len(warns), 2)


class TestJavaServerLog(unittest.TestCase):
    """Test parsing Java server logs"""

    def setUp(self):
        self.log_path = SAMPLE_FILES['java_server']
        self.assertTrue(os.path.exists(self.log_path), f"Sample file not found: {self.log_path}")

    def test_collect_java_logs(self):
        """Test collecting Java server log entries"""
        entries, counts = collect_lines(self.log_path)
        
        self.assertGreater(len(entries), 0)
        self.assertEqual(counts.get("INFO", 0), 2)
        self.assertEqual(counts.get("WARN", 0), 1)
        self.assertEqual(counts.get("ERROR", 0), 1)

    def test_java_format_detection(self):
        """Test that Java format [LEVEL] timestamp service - message is detected"""
        entries, _ = collect_lines(self.log_path)
        
        # Should have source/service names
        sources = [e.get("source") for e in entries if e.get("source")]
        self.assertGreater(len(sources), 0)

    def test_java_null_pointer_hint(self):
        """Test hint for Java NullPointerException"""
        entries, _ = collect_lines(self.log_path)
        
        error_entries = [e for e in entries if "NullPointerException" in e.get("message", "")]
        self.assertEqual(len(error_entries), 1)
        
        hint = error_entries[0]["hint"]
        self.assertIn("null", hint.lower())


class TestProdServerLog(unittest.TestCase):
    """Test parsing production server logs - most comprehensive"""

    def setUp(self):
        self.log_path = SAMPLE_FILES['prod_server']
        self.assertTrue(os.path.exists(self.log_path), f"Sample file not found: {self.log_path}")

    def test_collect_prod_logs(self):
        """Test collecting production log entries"""
        entries, counts = collect_lines(self.log_path)
        
        self.assertEqual(len(entries), 11)
        self.assertEqual(counts.get("INFO", 0), 3)
        self.assertEqual(counts.get("WARN", 0), 2)
        self.assertEqual(counts.get("ERROR", 0), 6)

    def test_prod_server_multiple_errors(self):
        """Test detection of multiple error types"""
        entries, _ = collect_lines(self.log_path, level="ERROR")
        
        self.assertEqual(len(entries), 6)
        
        # Check for different error patterns
        messages = [e["message"] for e in entries]
        self.assertTrue(any("Connection refused" in m for m in messages))
        self.assertTrue(any("TypeError" in m for m in messages))
        self.assertTrue(any("Disk full" in m for m in messages))
        self.assertTrue(any("OutOfMemoryError" in m for m in messages))

    def test_prod_server_memory_error_hint(self):
        """Test memory error detection"""
        entries, _ = collect_lines(self.log_path)
        
        memory_errors = [e for e in entries if "OutOfMemoryError" in e["message"]]
        self.assertEqual(len(memory_errors), 1)
        
        hint = memory_errors[0]["hint"]
        self.assertIn("memory", hint.lower())

    def test_prod_server_connection_error_hint(self):
        """Test connection error detection"""
        entries, _ = collect_lines(self.log_path)
        
        conn_errors = [e for e in entries if "Connection refused" in e["message"]]
        self.assertEqual(len(conn_errors), 1)
        
        hint = conn_errors[0]["hint"]
        self.assertIn("unreachable", hint.lower())

    def test_prod_server_severity_sorting(self):
        """Test that errors are prioritized over warnings"""
        entries, counts = collect_lines(self.log_path)
        
        # Sort entries as the tool does
        sorted_entries = sorted(entries, key=lambda x: (-LEVEL_ORDER.get(x["level"], 0), x["timestamp"]))
        
        # First entries should be ERROR
        top_3 = sorted_entries[:3]
        self.assertTrue(all(e["level"] == "ERROR" for e in top_3))

    def test_prod_server_summary(self):
        """Test generating comprehensive summary"""
        entries, counts = collect_lines(self.log_path)
        summary = heuristic_summary(entries, counts)
        
        self.assertIn("6 error(s)", summary)
        self.assertIn("2 warning(s)", summary)
        self.assertIn("3 info messages", summary)

    def test_prod_server_context_for_ai(self):
        """Test building context for AI analysis"""
        entries, counts = collect_lines(self.log_path)
        context = build_context(entries, counts, top_n=5)
        
        self.assertEqual(context["stats"]["ERROR"], 6)
        self.assertEqual(context["stats"]["WARN"], 2)
        self.assertEqual(context["stats"]["INFO"], 3)
        
        # Top 5 should include errors
        top_levels = [t["level"] for t in context["top"]]
        self.assertTrue(any(level == "ERROR" for level in top_levels))


class TestAppsLog(unittest.TestCase):
    """Test parsing generic application logs"""

    def setUp(self):
        self.log_path = SAMPLE_FILES['apps_log']
        self.assertTrue(os.path.exists(self.log_path), f"Sample file not found: {self.log_path}")

    def test_collect_apps_logs(self):
        """Test collecting application log entries"""
        entries, counts = collect_lines(self.log_path)
        
        self.assertGreater(len(entries), 0)
        self.assertEqual(counts.get("INFO", 0), 3)
        self.assertEqual(counts.get("WARN", 0), 1)
        self.assertEqual(counts.get("ERROR", 0), 3)

    def test_apps_timeout_detection(self):
        """Test timeout error detection"""
        entries, _ = collect_lines(self.log_path)
        
        timeout_errors = [e for e in entries if "timeout" in e["message"].lower()]
        self.assertGreater(len(timeout_errors), 0)
        
        hint = timeout_errors[0]["hint"]
        self.assertIn("timeout", hint.lower())


class TestVSCodeLogs(unittest.TestCase):
    """Test parsing VS Code editor logs"""

    def setUp(self):
        self.log_path = SAMPLE_FILES['vscode']
        self.assertTrue(os.path.exists(self.log_path), f"Sample file not found: {self.log_path}")

    def test_collect_vscode_logs(self):
        """Test collecting VS Code log entries"""
        entries, counts = collect_lines(self.log_path)
        
        self.assertGreater(len(entries), 0)
        # VS Code uses different format, should still parse
        self.assertTrue(any(e.get("message") for e in entries))

    def test_vscode_error_detection(self):
        """Test error detection in VS Code logs"""
        entries, _ = collect_lines(self.log_path, level="ERROR")
        
        self.assertGreater(len(entries), 0)

    def test_vscode_large_file(self):
        """Test parsing larger VS Code log file"""
        log_path = SAMPLE_FILES['vscode2']
        if os.path.exists(log_path):
            entries, counts = collect_lines(log_path)
            
            self.assertGreater(len(entries), 0)


class TestCrossFileParsing(unittest.TestCase):
    """Test parsing consistency across all sample files"""

    def test_all_samples_parse_successfully(self):
        """Verify all sample files can be parsed"""
        for name, path in SAMPLE_FILES.items():
            if os.path.exists(path):
                with self.subTest(file=name):
                    entries, counts = collect_lines(path)
                    self.assertGreater(len(entries), 0, f"Failed to parse {name}")
                    self.assertGreater(len(counts), 0, f"No log levels found in {name}")

    def test_all_samples_have_hints(self):
        """Verify hint generation works for all samples"""
        for name, path in SAMPLE_FILES.items():
            if os.path.exists(path):
                with self.subTest(file=name):
                    entries, _ = collect_lines(path)
                    
                    # All entries should have hints
                    for entry in entries:
                        self.assertIn("hint", entry)
                        self.assertIsNotNone(entry["hint"])
                        self.assertGreater(len(entry["hint"]), 0)

    def test_error_detection_consistency(self):
        """Test that error entries are consistently detected"""
        for name, path in SAMPLE_FILES.items():
            if os.path.exists(path):
                with self.subTest(file=name):
                    entries, counts = collect_lines(path)
                    
                    # Count ERROR level entries
                    error_entries = [e for e in entries if e["level"] == "ERROR"]
                    error_count = counts.get("ERROR", 0)
                    
                    # Counts should match
                    self.assertGreaterEqual(error_count, len(error_entries))

    def test_timestamp_parsing_across_formats(self):
        """Test that timestamps are parsed consistently"""
        expected_formats = {
            'python_dev': '2025-09-28',
            'android': '12-17',
            'dev_server': '2025-09-28',
            'java_server': '2025-09-28',
            'prod_server': '2025-09-28',
            'vscode': '2025-09-28',
        }
        
        for name, path in SAMPLE_FILES.items():
            if os.path.exists(path) and name in expected_formats:
                with self.subTest(file=name):
                    entries, _ = collect_lines(path)
                    
                    # Check that timestamps are parsed
                    parsed_entries = [e for e in entries if e.get("timestamp")]
                    self.assertGreater(len(parsed_entries), 0, f"No timestamps parsed in {name}")


class TestRealWorldScenarios(unittest.TestCase):
    """Test real-world usage scenarios"""

    def test_critical_errors_in_prod(self):
        """Find critical errors in production logs"""
        path = SAMPLE_FILES['prod_server']
        entries, counts = collect_lines(path)
        
        # Get top 3 errors
        error_entries = sorted(
            [e for e in entries if e["level"] == "ERROR"],
            key=lambda x: x["timestamp"]
        )
        
        self.assertGreaterEqual(len(error_entries), 3)

    def test_performance_issues_detection(self):
        """Detect performance issues in logs"""
        path = SAMPLE_FILES['prod_server']
        entries, _ = collect_lines(path)
        
        perf_issues = [e for e in entries if any(keyword in e["message"].lower() 
                       for keyword in ["latency", "delay", "timeout", "slow"])]
        
        # Prod server has latency mentioned
        self.assertGreater(len(perf_issues), 0)

    def test_summarize_multiple_services(self):
        """Summarize logs from multiple services"""
        paths = [SAMPLE_FILES['dev_server'], SAMPLE_FILES['java_server'], SAMPLE_FILES['prod_server']]
        
        combined_entries = []
        combined_counts = {}
        
        for path in paths:
            if os.path.exists(path):
                entries, counts = collect_lines(path)
                combined_entries.extend(entries)
                
                for level, count in counts.items():
                    combined_counts[level] = combined_counts.get(level, 0) + count
        
        # Should have aggregated data
        self.assertGreater(len(combined_entries), 0)
        self.assertGreater(combined_counts.get("ERROR", 0), 0)


if __name__ == '__main__':
    unittest.main()
