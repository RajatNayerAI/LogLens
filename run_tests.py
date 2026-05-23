#!/usr/bin/env python3
"""
Test Runner for LogLens
Executes all unit and integration tests with coverage reporting
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*70}")
    print(f"▶ {description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__) or '.')
    
    if result.returncode == 0:
        print(f"✓ {description} - PASSED")
    else:
        print(f"✗ {description} - FAILED (exit code: {result.returncode})")
    
    return result.returncode

def main():
    """Run all tests"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║          LogLens Test Suite - Running All Tests                   ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("❌ pytest not installed. Install with:")
        print("   pip install -r requirements-test.txt")
        return 1
    
    results = []
    
    # 1. Run unit tests for core module
    results.append(run_command(
        ['python', '-m', 'pytest', 'tests/test_loglens.py', '-v', '--tb=short'],
        'Unit Tests: Core Module (loglens.py)'
    ))
    
    # 2. Run unit tests for AI module
    results.append(run_command(
        ['python', '-m', 'pytest', 'tests/test_loglens_ai.py', '-v', '--tb=short'],
        'Unit Tests: AI Module (loglens_ai.py)'
    ))
    
    # 3. Run integration tests on sample logs
    results.append(run_command(
        ['python', '-m', 'pytest', 'tests/test_sample_logs.py', '-v', '--tb=short'],
        'Integration Tests: Sample Log Files'
    ))
    
    # 4. Run all tests together with coverage
    results.append(run_command(
        ['python', '-m', 'pytest', 'tests/', '-v', '--cov=Code', '--cov-report=term-missing', '--cov-report=html'],
        'Full Test Suite with Coverage Report'
    ))
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}\n")
    
    test_names = [
        'Core Module Tests',
        'AI Module Tests',
        'Integration Tests',
        'Full Suite with Coverage'
    ]
    
    passed = sum(1 for r in results if r == 0)
    failed = sum(1 for r in results if r != 0)
    
    for name, result in zip(test_names, results):
        status = "✓ PASSED" if result == 0 else "✗ FAILED"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n✓ All tests passed!")
        print("\nCoverage report generated in: htmlcov/index.html")
        print("Open it in a browser to view detailed coverage analysis.")
    else:
        print(f"\n✗ {failed} test suite(s) failed")
    
    return 1 if failed > 0 else 0

if __name__ == '__main__':
    sys.exit(main())
