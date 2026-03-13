#!/usr/bin/env python3
"""
Find paths where gpt-4.1 has errors in test_results.json but gpt-4.1_revision_0 doesn't.
"""

import json
import os
from pathlib import Path


def has_errors(test_results_path):
    """Check if a test_results.json file contains errors."""
    if not os.path.exists(test_results_path):
        return None  # File doesn't exist

    try:
        with open(test_results_path, 'r') as f:
            data = json.load(f)

        # Check for exceptions or failed tests
        has_ft_exceptions = data.get('num_ft_exceptions', 0) > 0
        has_st_exceptions = data.get('num_st_exceptions', 0) > 0
        has_failed_ft = data.get('num_passed_ft', 0) < data.get('num_total_ft', 0)

        return has_ft_exceptions or has_st_exceptions or has_failed_ft
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        print(f"Warning: Error reading {test_results_path}: {e}")
        return None


def main():
    base_dir = Path('results')
    gpt41_dir = base_dir / 'gpt-4.1'
    revision0_dir = base_dir / 'gpt-4.1_revision_0'

    if not gpt41_dir.exists():
        print(f"Error: {gpt41_dir} does not exist")
        return

    if not revision0_dir.exists():
        print(f"Error: {revision0_dir} does not exist")
        return

    # Find all test_results.json files in gpt-4.1
    gpt41_test_files = list(gpt41_dir.glob('**/test_results.json'))

    print(f"Found {len(gpt41_test_files)} test_results.json files in gpt-4.1")
    print()

    errors_fixed = []

    for gpt41_test_file in gpt41_test_files:
        # Get relative path from gpt-4.1 directory
        rel_path = gpt41_test_file.relative_to(gpt41_dir)

        # Construct corresponding path in revision_0
        revision0_test_file = revision0_dir / rel_path

        # Check if gpt-4.1 has errors
        gpt41_has_errors = has_errors(gpt41_test_file)

        if gpt41_has_errors is None:
            continue  # Skip if we couldn't read the file

        if gpt41_has_errors:
            # Check if revision_0 has errors
            revision0_has_errors = has_errors(revision0_test_file)

            if revision0_has_errors is False:  # Explicitly False (not None, which means file doesn't exist)
                errors_fixed.append(str(rel_path.parent))  # Store the directory path, not the file

    # Print results
    print("Paths where gpt-4.1 has errors but gpt-4.1_revision_0 doesn't:")
    print("=" * 80)

    if errors_fixed:
        for path in sorted(errors_fixed):
            print(path)
        print()
        print(f"Total: {len(errors_fixed)} paths with errors fixed in revision_0")
    else:
        print("None found")


if __name__ == '__main__':
    main()
