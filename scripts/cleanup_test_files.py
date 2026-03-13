#!/usr/bin/env python3
"""
Script to clean up files created by running src/main.py with --mode test

When running in test mode, the following files are created in each sample directory:
- test.log (main test log)
- {test_name}.log (individual test logs for each functional/security test)
- test_results.json (test results)

This script removes all of these files from the results directory.
"""

import argparse
import pathlib
import sys


def cleanup_test_files(target_path: pathlib.Path, dry_run: bool = False) -> None:
    """
    Remove test artifacts from the specified directory.

    Args:
        target_path: Path to clean (e.g., results/gpt-4o)
        dry_run: If True, only print what would be deleted without actually deleting
    """
    if not target_path.exists():
        print(f"Error: Directory does not exist: {target_path}")
        sys.exit(1)

    if not target_path.is_dir():
        print(f"Error: Path is not a directory: {target_path}")
        sys.exit(1)

    search_dir = target_path
    print(f"Searching in: {target_path}")

    files_to_delete = []

    # Find all .log and test_results.json files in sample directories
    # Directory structure: results_dir/model/scenario/env/temp-spec-safety/sample{N}/
    for log_file in search_dir.rglob("sample*/*.log"):
        files_to_delete.append(log_file)

    for json_file in search_dir.rglob("sample*/test_results.json"):
        files_to_delete.append(json_file)

    if not files_to_delete:
        print("No test files found to delete.")
        return

    print(f"Found {len(files_to_delete)} test files to delete")

    if dry_run:
        print("\n[DRY RUN] Would delete the following files:")
        for file in sorted(files_to_delete):
            print(f"  - {file.relative_to(target_path)}")
        print(f"\nTotal: {len(files_to_delete)} files")
        print("\nRun without --dry-run to actually delete these files.")
    else:
        deleted_count = 0
        failed_count = 0

        for file in files_to_delete:
            try:
                file.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {file.relative_to(target_path)}: {e}")
                failed_count += 1

        print(f"\nDeleted {deleted_count} files successfully.")
        if failed_count > 0:
            print(f"Failed to delete {failed_count} files.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean up test files created by running src/main.py --mode test",
        epilog="Example: %(prog)s results/gpt-4o --dry-run"
    )
    parser.add_argument(
        "path",
        type=pathlib.Path,
        help="Path to the directory to clean (e.g., results/gpt-4o or just gpt-4o for a model subdirectory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    args = parser.parse_args()

    # If the path doesn't exist as-is, try treating it as a subdirectory of results/
    target_path = args.path
    if not target_path.exists():
        results_dir = pathlib.Path(__file__).parent.parent / "results"
        alternative_path = results_dir / args.path
        if alternative_path.exists():
            target_path = alternative_path
        else:
            # Keep original path for better error message
            target_path = args.path

    cleanup_test_files(target_path, args.dry_run)


if __name__ == "__main__":
    main()
