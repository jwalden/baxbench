#!/usr/bin/env python3
"""
Analyze test.log files to find common error patterns.

Usage:
    python analyze_test_logs.py <path_to_results_dir>
    python analyze_test_logs.py results/gpt-5-chat-latest
    python analyze_test_logs.py results/gpt-4o --top 20
"""

import argparse
import re
import pathlib
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set


class ErrorPattern:
    """Represents a categorized error pattern."""

    def __init__(self, name: str, pattern: str, description: str):
        self.name = name
        self.pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        self.description = description
        self.occurrences = 0
        self.files = set()
        self.examples = []

    def add_match(self, file_path: str, match_text: str):
        self.occurrences += 1
        self.files.add(file_path)
        if len(self.examples) < 5:  # Keep up to 5 examples
            self.examples.append((file_path, match_text))


# Define error patterns to detect
ERROR_PATTERNS = [
    ErrorPattern(
        "Connection Reset",
        r"(Connection reset by peer|RemoteDisconnected|Connection aborted)",
        "Server connection reset during startup or requests"
    ),
    ErrorPattern(
        "Server Startup Timeout",
        r"Server did not start in time",
        "Server failed to become responsive within timeout period"
    ),
    ErrorPattern(
        "Container Not Found",
        r"docker\.errors\.NotFound.*No such container",
        "Docker container disappeared or crashed"
    ),
    ErrorPattern(
        "Functional Test Failed",
        r"Functional test .+ failed",
        "Functional test execution failure"
    ),
    ErrorPattern(
        "Security Test Failed",
        r"Security test .+ failed",
        "Security vulnerability test failure"
    ),
    ErrorPattern(
        "DisallowedHost",
        r"(Invalid HTTP_HOST header|DisallowedHost)",
        "Django ALLOWED_HOSTS configuration error"
    ),
    ErrorPattern(
        "404 Not Found",
        r'"(GET|POST|PUT|DELETE|PATCH) [^"]+HTTP/1\.[01]" 404',
        "HTTP endpoint not found"
    ),
    ErrorPattern(
        "500 Internal Server Error",
        r'"(GET|POST|PUT|DELETE|PATCH) [^"]+HTTP/1\.[01]" 500',
        "HTTP internal server error"
    ),
    ErrorPattern(
        "Python Exception",
        r"(Traceback \(most recent call last\)|raise \w+Error)",
        "Python exception or traceback"
    ),
    ErrorPattern(
        "RuntimeWarning",
        r"RuntimeWarning:",
        "Python runtime warnings"
    ),
    ErrorPattern(
        "Syntax Error",
        r"(SyntaxError|Syntax Error)",
        "Syntax errors in code or data"
    ),
    ErrorPattern(
        "Import Error",
        r"(ImportError|ModuleNotFoundError)",
        "Python module import failures"
    ),
    ErrorPattern(
        "Database Error",
        r"(DatabaseError|OperationalError|IntegrityError)",
        "Database operation failures"
    ),
    ErrorPattern(
        "Permission Denied",
        r"Permission denied",
        "File or resource permission errors"
    ),
    ErrorPattern(
        "Timeout Error",
        r"(TimeoutError|timed out|timeout)",
        "Operation timeout errors"
    ),
]


def find_test_logs(base_path: pathlib.Path) -> List[pathlib.Path]:
    """Find all test.log files under the given path."""
    return sorted(base_path.rglob("test.log"))


def analyze_log_file(log_path: pathlib.Path, patterns: List[ErrorPattern]) -> None:
    """Analyze a single log file for error patterns."""
    try:
        content = log_path.read_text(errors='ignore')

        for pattern in patterns:
            matches = pattern.pattern.finditer(content)
            for match in matches:
                # Get surrounding context (up to 200 chars)
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                context = content[start:end].strip()

                pattern.add_match(str(log_path), context)

    except Exception as e:
        print(f"Warning: Could not read {log_path}: {e}")


def print_summary(patterns: List[ErrorPattern], total_files: int, top_n: int = 15):
    """Print analysis summary."""

    # Sort patterns by occurrence count
    sorted_patterns = sorted(patterns, key=lambda p: p.occurrences, reverse=True)

    # Filter to only patterns that matched
    matched_patterns = [p for p in sorted_patterns if p.occurrences > 0]

    # Calculate total errors
    total_errors = sum(p.occurrences for p in matched_patterns)

    print("=" * 80)
    print("TEST LOG ERROR ANALYSIS REPORT")
    print("=" * 80)
    print()
    print(f"Total files analyzed: {total_files}")
    print(f"Total error occurrences: {total_errors:,}")
    print(f"Unique error patterns found: {len(matched_patterns)}")
    print()
    print("=" * 80)
    print(f"TOP {min(top_n, len(matched_patterns))} ERROR PATTERNS")
    print("=" * 80)
    print()

    for i, pattern in enumerate(matched_patterns[:top_n], 1):
        percentage = (pattern.occurrences / total_errors * 100) if total_errors > 0 else 0
        files_affected_pct = (len(pattern.files) / total_files * 100) if total_files > 0 else 0

        print(f"{i}. {pattern.name}")
        print(f"   Occurrences: {pattern.occurrences:,} ({percentage:.1f}% of all errors)")
        print(f"   Files affected: {len(pattern.files)}/{total_files} ({files_affected_pct:.1f}%)")
        print(f"   Description: {pattern.description}")

        if pattern.examples:
            print(f"   Example:")
            example_file, example_text = pattern.examples[0]
            # Truncate example to fit nicely
            example_lines = example_text.split('\n')
            for line in example_lines[:3]:
                if line.strip():
                    print(f"      {line[:100]}")

            print(f"   Sample files:")
            for file_path, _ in pattern.examples[:3]:
                print(f"      {file_path}")

        print()


def print_detailed_report(patterns: List[ErrorPattern], output_file: str = None):
    """Print or save detailed report with all examples."""

    sorted_patterns = sorted(patterns, key=lambda p: p.occurrences, reverse=True)
    matched_patterns = [p for p in sorted_patterns if p.occurrences > 0]

    lines = []
    lines.append("=" * 80)
    lines.append("DETAILED ERROR ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append("")

    for pattern in matched_patterns:
        lines.append(f"\n{'=' * 80}")
        lines.append(f"{pattern.name}")
        lines.append(f"{'=' * 80}")
        lines.append(f"Occurrences: {pattern.occurrences:,}")
        lines.append(f"Files affected: {len(pattern.files)}")
        lines.append(f"Description: {pattern.description}")
        lines.append("")
        lines.append("Examples:")
        lines.append("-" * 80)

        for file_path, example in pattern.examples:
            lines.append(f"\nFile: {file_path}")
            lines.append(example[:500])  # Limit example length
            lines.append("-" * 80)

        lines.append("")
        lines.append("All affected files:")
        for file_path in sorted(pattern.files)[:20]:  # Limit to first 20
            lines.append(f"  - {file_path}")
        if len(pattern.files) > 20:
            lines.append(f"  ... and {len(pattern.files) - 20} more files")
        lines.append("")

    report = "\n".join(lines)

    if output_file:
        pathlib.Path(output_file).write_text(report)
        print(f"\nDetailed report saved to: {output_file}")
    else:
        print(report)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze test.log files for common error patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_test_logs.py results/gpt-5-chat-latest
  python analyze_test_logs.py results/gpt-4o --top 20
  python analyze_test_logs.py results/claude-sonnet-4 --detailed error_report.txt
        """
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to results directory containing test.log files"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=15,
        help="Number of top error patterns to show (default: 15)"
    )
    parser.add_argument(
        "--detailed",
        type=str,
        metavar="FILE",
        help="Generate detailed report and save to FILE"
    )

    args = parser.parse_args()

    base_path = pathlib.Path(args.path)

    if not base_path.exists() or not base_path.is_dir():
        print(f"Error: Path '{args.path}' does not exist or is not a directory")
        return 1

    print(f"Searching for test.log files in {base_path}...")
    log_files = find_test_logs(base_path)

    if not log_files:
        print(f"No test.log files found in {base_path}")
        return 1

    print(f"Found {len(log_files)} test.log files")
    print("Analyzing...")

    # Analyze all log files
    for i, log_file in enumerate(log_files, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(log_files)} files...")
        analyze_log_file(log_file, ERROR_PATTERNS)

    print(f"Analysis complete!\n")

    # Print summary
    print_summary(ERROR_PATTERNS, len(log_files), args.top)

    # Print detailed report if requested
    if args.detailed:
        print_detailed_report(ERROR_PATTERNS, args.detailed)

    return 0


if __name__ == "__main__":
    exit(main())
