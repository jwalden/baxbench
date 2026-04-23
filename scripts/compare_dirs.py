#!/usr/bin/env python3

import sys
from pathlib import Path
from find_ft_exceptions import find_ft_exceptions


def normalize(path):
    """
    Remove the first two path components.
    Example:
        results/gpt-4.1/Calculator/...  ->  Calculator/...
    """
    p = Path(path)
    parts = p.parts[2:]  # drop first two components
    return str(Path(*parts))


def main():
    if len(sys.argv) != 3:
        print("Usage: python compare_ft_exceptions.py <initial_dir> <revised_dir>")
        sys.exit(1)

    initial_dir = sys.argv[1]
    revised_dir = sys.argv[2]

    # Run your function
    initial_results = find_ft_exceptions(initial_dir)
    revised_results = find_ft_exceptions(revised_dir)

    # Normalize directory paths
    initial_paths = set(normalize(path) for path, _ in initial_results)
    revised_paths = set(normalize(path) for path, _ in revised_results)

    # Differences
    new_dirs = revised_paths - initial_paths

    print("\nNew FT-exception directories (normalized):\n")
    if not new_dirs:
        print("(None)")
    else:
        for d in sorted(new_dirs):
            print(d)

    print(f"\nTotal new directories: {len(new_dirs)}")


if __name__ == "__main__":
    main()
