#!/usr/bin/env python3
"""ELVIS Test Runner - Comprehensive test execution with modern tooling

This script provides a unified interface for running different categories
of tests with appropriate configurations and reporting.

Usage:
    python run_tests.py --help                    # Show help
    python run_tests.py --unit                    # Run unit tests only
    python run_tests.py --integration             # Run integration tests only
    python run_tests.py --performance             # Run performance tests only
    python run_tests.py --property                # Run property-based tests only
    python run_tests.py --all                     # Run all tests
    python run_tests.py --fast                    # Run fast tests (exclude slow)
    python run_tests.py --coverage                # Run with detailed coverage
    python run_tests.py --profile                 # Run with profiling
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


class TestRunner:
    """Manages test execution with different configurations."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_dir = project_root / "tests"

    def run_unit_tests(self, coverage: bool = True, verbose: bool = True) -> int:
        """Run unit tests with optimized settings."""
        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/unit/",
            "--tb=short",
            "-v" if verbose else "-q",
        ]

        if coverage:
            cmd.extend(
                [
                    "--cov=elvis",
                    "--cov-report=term-missing",
                    "--cov-report=html:htmlcov/unit",
                    "--cov-branch",
                ]
            )

        cmd.extend(["--durations=5", "-m", "not slow"])

        print("🧪 Running unit tests...")
        return self._execute_command(cmd)

    def run_integration_tests(self, verbose: bool = True) -> int:
        """Run integration tests."""
        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/integration/",
            "--tb=short",
            "-v" if verbose else "-q",
            "--durations=10",
        ]

        print("🔗 Running integration tests...")
        return self._execute_command(cmd)

    def run_performance_tests(self, verbose: bool = True) -> int:
        """Run performance regression tests."""
        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/performance/",
            "--tb=short",
            "-v" if verbose else "-q",
            "--durations=0",  # Show all durations
            "-m",
            "performance",
        ]

        print("⚡ Running performance regression tests...")
        return self._execute_command(cmd)

    def run_property_tests(self, verbose: bool = True) -> int:
        """Run property-based tests with Hypothesis."""
        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/unit/test_property_based.py",
            "--tb=short",
            "-v" if verbose else "-q",
            "--hypothesis-show-statistics",
            "--hypothesis-seed=42",  # Reproducible runs
        ]

        print("🔍 Running property-based tests...")
        return self._execute_command(cmd)

    def run_fast_tests(self, coverage: bool = False) -> int:
        """Run fast tests only (exclude slow markers)."""
        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/unit/",
            "tests/integration/",
            "--tb=short",
            "-v",
            "-m",
            "not slow",
            "--durations=5",
        ]

        if coverage:
            cmd.extend(["--cov=elvis", "--cov-report=term-missing"])

        print("🚀 Running fast tests only...")
        return self._execute_command(cmd)

    def run_all_tests(self, coverage: bool = True) -> int:
        """Run comprehensive test suite."""
        cmd = ["python", "-m", "pytest", "tests/", "--tb=short", "-v"]

        if coverage:
            cmd.extend(
                [
                    "--cov=elvis",
                    "--cov-report=term-missing",
                    "--cov-report=html:htmlcov/all",
                    "--cov-report=xml:coverage.xml",
                    "--cov-branch",
                    "--cov-fail-under=75",
                ]
            )

        cmd.extend(["--durations=10", "--hypothesis-show-statistics"])

        print("🎯 Running comprehensive test suite...")
        return self._execute_command(cmd)

    def run_with_profile(self, test_path: str = "tests/unit/") -> int:
        """Run tests with profiling enabled."""
        cmd = ["python", "-m", "pytest", test_path, "--tb=short", "--profile", "--durations=0"]

        print("📊 Running tests with profiling...")
        return self._execute_command(cmd)

    def run_coverage_report(self) -> int:
        """Generate detailed coverage report."""
        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/unit/",
            "tests/integration/",
            "--cov=elvis",
            "--cov-report=html:htmlcov/detailed",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term-missing",
            "--cov-branch",
            "--cov-fail-under=80",
            "-v",
        ]

        print("📈 Generating detailed coverage report...")
        result = self._execute_command(cmd)

        if result == 0:
            print("\n✅ Coverage report generated:")
            print("   HTML: htmlcov/detailed/index.html")
            print("   XML:  coverage.xml")

        return result

    def run_type_check(self) -> int:
        """Run type checking with mypy."""
        cmd = ["python", "-m", "mypy", "elvis/", "--config-file", "pyproject.toml"]

        print("🔍 Running type checking...")
        return self._execute_command(cmd)

    def run_lint_check(self) -> int:
        """Run code quality checks."""
        print("🧹 Running code quality checks...")

        # Run multiple linters
        commands = [
            (["python", "-m", "black", "--check", "elvis/", "tests/"], "Black formatting"),
            (["python", "-m", "isort", "--check", "elvis/", "tests/"], "Import sorting"),
            (["python", "-m", "flake8", "elvis/", "tests/"], "Flake8 linting"),
        ]

        overall_result = 0
        for cmd, name in commands:
            print(f"  Running {name}...")
            result = self._execute_command(cmd, show_output=False)
            if result != 0:
                overall_result = result
                print(f"    ❌ {name} failed")
            else:
                print(f"    ✅ {name} passed")

        return overall_result

    def _execute_command(self, cmd: list[str], show_output: bool = True) -> int:
        """Execute a command and return exit code."""
        if show_output:
            print(f"Executing: {' '.join(cmd)}")

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd, check=False, cwd=self.project_root, capture_output=not show_output, text=True
            )

            duration = time.time() - start_time

            if show_output:
                if result.returncode == 0:
                    print(f"✅ Command completed successfully in {duration:.1f}s")
                else:
                    print(
                        f"❌ Command failed with exit code {result.returncode} after {duration:.1f}s"
                    )

            return result.returncode

        except Exception as e:
            print(f"❌ Error executing command: {e}")
            return 1


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="ELVIS Test Runner - Comprehensive test execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --unit --coverage      # Unit tests with coverage
  python run_tests.py --fast                 # Quick test run
  python run_tests.py --all                  # Full test suite
  python run_tests.py --performance          # Performance benchmarks
  python run_tests.py --property             # Property-based tests
        """,
    )

    # Test categories
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--property", action="store_true", help="Run property-based tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only")

    # Options
    parser.add_argument("--coverage", action="store_true", help="Include coverage reporting")
    parser.add_argument("--profile", action="store_true", help="Run with profiling")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    parser.add_argument("--typecheck", action="store_true", help="Run type checking")
    parser.add_argument("--lint", action="store_true", help="Run code quality checks")

    args = parser.parse_args()

    # Find project root
    project_root = Path(__file__).parent
    runner = TestRunner(project_root)

    # Default to fast tests if no specific category selected
    if not any([args.unit, args.integration, args.performance, args.property, args.all]):
        args.fast = True

    exit_code = 0
    verbose = not args.quiet

    try:
        if args.lint:
            exit_code = max(exit_code, runner.run_lint_check())

        if args.typecheck:
            exit_code = max(exit_code, runner.run_type_check())

        if args.unit:
            exit_code = max(
                exit_code, runner.run_unit_tests(coverage=args.coverage, verbose=verbose)
            )

        if args.integration:
            exit_code = max(exit_code, runner.run_integration_tests(verbose=verbose))

        if args.performance:
            exit_code = max(exit_code, runner.run_performance_tests(verbose=verbose))

        if args.property:
            exit_code = max(exit_code, runner.run_property_tests(verbose=verbose))

        if args.fast:
            exit_code = max(exit_code, runner.run_fast_tests(coverage=args.coverage))

        if args.all:
            exit_code = max(exit_code, runner.run_all_tests(coverage=args.coverage))

        if args.coverage and not any([args.unit, args.all, args.fast]):
            exit_code = max(exit_code, runner.run_coverage_report())

        # Summary
        if exit_code == 0:
            print("\n🎉 All tests passed successfully!")
        else:
            print(f"\n💥 Some tests failed (exit code: {exit_code})")

    except KeyboardInterrupt:
        print("\n⚠️  Test run interrupted by user")
        exit_code = 130

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
