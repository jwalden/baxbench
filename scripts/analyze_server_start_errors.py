#!/usr/bin/env python3
"""
Analyze test.log files for "Server did not start in time" errors
and categorize them by the underlying Python exception.
"""

import argparse
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional


def extract_python_error(log_content: str, error_position: int) -> Optional[str]:
    """
    Extract the Python error type from container logs following a
    "Server did not start in time" error.

    Args:
        log_content: The full log file content
        error_position: Position where "Server did not start in time" was found

    Returns:
        The Python exception type (e.g., "ImportError", "SyntaxError") or None
    """
    # Look for "container logs:" after the error
    container_logs_match = re.search(
        r'container logs:',
        log_content[error_position:error_position + 500]
    )

    if not container_logs_match:
        return None

    # Start searching after "container logs:"
    search_start = error_position + container_logs_match.end()

    # Look for the traceback section (up to 5000 characters should be enough)
    traceback_section = log_content[search_start:search_start + 5000]

    # Find Python exception patterns like "ImportError:", "SyntaxError:", etc.
    # These typically appear at the end of a traceback
    # Also handle module-qualified exceptions like "pydantic.errors.PydanticUserError"
    exception_pattern = r'^(?:[\w.]+\.)?(\w+Error|\w+Exception|KeyboardInterrupt|SystemExit|GeneratorExit):\s*(.*)$'

    # Look through the section line by line
    lines = traceback_section.split('\n')

    # Track if we're in a traceback
    in_traceback = False
    last_exception = None

    for line in lines:
        # Check if this line starts a traceback
        if line.strip().startswith('Traceback (most recent call last):'):
            in_traceback = True
            last_exception = None
            continue

        # If we hit another INFO/ERROR/WARNING line, we've left the container logs
        if re.match(r'^(INFO|ERROR|WARNING|DEBUG)\s+\d{4}-\d{2}-\d{2}', line):
            break

        if in_traceback:
            # Look for exception lines (with or without module path)
            match = re.match(exception_pattern, line.strip())
            if match:
                last_exception = match.group(1)
            # Also check for exceptions without colons (just the type name on a line)
            elif line.strip() and not line.startswith(' '):
                # Check if line is just an exception name (possibly module-qualified)
                simple_exception = re.match(r'^(?:[\w.]+\.)?(\w+Error|\w+Exception)$', line.strip())
                if simple_exception:
                    last_exception = simple_exception.group(1)

    return last_exception


def analyze_test_logs(base_path: Path) -> Dict[str, List[Path]]:
    """
    Analyze all test.log files under the given path for server start errors.

    Args:
        base_path: Root directory to search for test.log files

    Returns:
        Dictionary mapping error types to lists of file paths
    """
    error_files = defaultdict(list)

    # Find all test.log files
    test_log_files = list(base_path.rglob('test.log'))

    print(f"Found {len(test_log_files)} test.log files")
    print(f"Analyzing files for 'Server did not start in time' errors...\n")

    for log_file in test_log_files:
        try:
            content = log_file.read_text(encoding='utf-8', errors='ignore')

            # Find all occurrences of "Server did not start in time"
            pattern = r'Server did not start in time'
            matches = list(re.finditer(pattern, content))

            if matches:
                # For each occurrence, try to extract the Python error
                for match in matches:
                    error_type = extract_python_error(content, match.start())

                    if error_type:
                        # Only add the file once per error type
                        if log_file not in error_files[error_type]:
                            error_files[error_type].append(log_file)
                        break  # Found an error for this file, move to next file
                else:
                    # No Python error found, categorize as "Unknown"
                    if log_file not in error_files["Unknown"]:
                        error_files["Unknown"].append(log_file)

        except Exception as e:
            print(f"Warning: Could not process {log_file}: {e}")

    return error_files


def generate_report(error_files: Dict[str, List[Path]], base_path: Path, output_file: Optional[Path] = None):
    """
    Generate a report of the analysis results.

    Args:
        error_files: Dictionary mapping error types to file paths
        base_path: Base path used for analysis (for relative path calculation)
        output_file: Optional file path to write the report to
    """
    total_files = sum(len(files) for files in error_files.values())

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("SERVER START ERROR ANALYSIS REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"\nAnalyzed path: {base_path}")
    report_lines.append(f"\nTotal test.log files with 'Server did not start in time': {total_files}")
    report_lines.append(f"Number of distinct error types: {len(error_files)}")
    report_lines.append("\n" + "=" * 80)
    report_lines.append("ERROR BREAKDOWN")
    report_lines.append("=" * 80)

    # Sort by count (descending)
    sorted_errors = sorted(error_files.items(), key=lambda x: len(x[1]), reverse=True)

    for error_type, files in sorted_errors:
        report_lines.append(f"\n{error_type}: {len(files)} occurrence(s)")
        report_lines.append("-" * 80)

        # Sort files alphabetically
        for file_path in sorted(files):
            # Make path relative to base_path for cleaner output
            try:
                rel_path = file_path.relative_to(base_path)
            except ValueError:
                rel_path = file_path
            report_lines.append(f"  - {rel_path}")

    report_lines.append("\n" + "=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)

    report_text = "\n".join(report_lines)

    # Print to console
    print(report_text)

    # Optionally write to file
    if output_file:
        output_file.write_text(report_text, encoding='utf-8')
        print(f"\nReport saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze test.log files for server start errors and categorize by Python exception type'
    )
    parser.add_argument(
        'path',
        type=str,
        help='Path to search for test.log files (e.g., results/gpt-4.1)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file path for the report (optional, defaults to console only)'
    )

    args = parser.parse_args()

    base_path = Path(args.path)

    if not base_path.exists():
        print(f"Error: Path '{base_path}' does not exist")
        return 1

    if not base_path.is_dir():
        print(f"Error: Path '{base_path}' is not a directory")
        return 1

    # Analyze the logs
    error_files = analyze_test_logs(base_path)

    # Generate report
    output_path = Path(args.output) if args.output else None
    generate_report(error_files, base_path, output_path)

    return 0


if __name__ == '__main__':
    exit(main())
