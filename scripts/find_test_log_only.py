#!/usr/bin/env python3
"""Find all subdirectories of results/ that contain test.log but no other .log files."""

import argparse
from pathlib import Path


def find_test_log_only_dirs(results_dir: Path) -> list[Path]:
    """Find directories containing only test.log and no other .log files."""
    dirs_with_only_test_log = []

    for test_log in results_dir.rglob("test.log"):
        parent_dir = test_log.parent
        log_files = list(parent_dir.glob("*.log"))

        # If test.log is the only .log file in the directory
        if len(log_files) == 1 and log_files[0].name == "test.log":
            dirs_with_only_test_log.append(parent_dir)

    return sorted(dirs_with_only_test_log)


def main():
    parser = argparse.ArgumentParser(
        description="Find subdirectories with test.log but no other .log files"
    )
    parser.add_argument(
        "results_dir",
        nargs="?",
        default="results",
        help="Path to results directory (default: results)",
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"Error: Directory '{results_dir}' does not exist")
        return 1

    dirs = find_test_log_only_dirs(results_dir)
    for d in dirs:
        print(d)

    print(f"\nTotal: {len(dirs)} directories", file=__import__("sys").stderr)
    return 0


if __name__ == "__main__":
    exit(main())
