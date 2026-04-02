#!/usr/bin/env python3
"""
Find subdirectories containing test_results.json files with functional test exceptions.

Usage:
    python find_ft_exceptions.py <results_directory>

Example:
    python find_ft_exceptions.py results/gpt-4.1_initial
"""

import json
import sys
from pathlib import Path


def find_ft_exceptions(base_dir):
    """
    Find all subdirectories containing test_results.json with ft exceptions.

    Args:
        base_dir: Base directory to search (e.g., 'results/gpt-4.1_initial')

    Returns:
        List of tuples (path, num_ft_exceptions)
    """
    base_path = Path(base_dir)

    if not base_path.exists():
        print(f"Error: Directory '{base_dir}' does not exist", file=sys.stderr)
        return []

    results = []

    # Find all test_results.json files
    for test_file in base_path.rglob('test_results.json'):
        try:
            with open(test_file, 'r') as f:
                data = json.load(f)

            # Check if there are ft exceptions
            num_ft_exceptions = data.get('num_ft_exceptions', 0)
            if num_ft_exceptions > 0:
                # Get the directory containing the test_results.json file
                subdir = test_file.parent
                results.append((str(subdir), num_ft_exceptions))

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read {test_file}: {e}", file=sys.stderr)
            continue

    return results


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    base_dir = sys.argv[1]

    results = find_ft_exceptions(base_dir)

    if not results:
        print(f"No test_results.json files with ft exceptions found in {base_dir}")
        return

    # Sort results by path
    results.sort()

    print(f"Found {len(results)} subdirectories with ft exceptions:\n")

    for path, num_exceptions in results:
        print(f"{path} ({num_exceptions} exception{'s' if num_exceptions != 1 else ''})")

    print(f"\nTotal: {len(results)} subdirectories")


if __name__ == '__main__':
    main()
