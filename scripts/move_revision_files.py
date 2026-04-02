#!/usr/bin/env python3
"""
Script to copy files from revision<n>/code/ directories to their parent sample<m>/ directories
and then copy the entire model directory to a destination location.

This script:
1. Copies files from revision<n>/code/ to sample<m>/code/ (preserving the code directory)
2. Copies the entire model directory from revision_results/ to the specified destination
3. Renames the model directory to model_name_revision_n
4. Removes all revision folders in the destination

Usage: python move_revision_files.py <model_name> <destination_path> [--revision N] [--sample M]
Example: python move_revision_files.py gpt-4o ../research/baxbench/results --revision 0 --sample 0
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


def copy_files_from_revision_to_sample_in_destination(destination_model_path, revision_num, sample_num):
    """
    Copy all files from revision<n>/code/ to sample<m>/code/ directory in the destination.
    
    Args:
        destination_model_path: Path to the copied model directory
        revision_num: Revision number to copy from
        sample_num: Sample number to copy to
    """
    revision_name = f"revision{revision_num}"
    sample_name = f"sample{sample_num}"
    
    print(f"Copying files from {revision_name}/code directories in destination: {destination_model_path}")
    
    # Find all revision<n>/code directories in the destination
    revision_dirs = []
    for root, dirs, files in os.walk(destination_model_path):
        if revision_name in root and 'code' in root:
            revision_path = Path(root)
            # Only include if this is exactly the revision<n>/code directory (not a subdirectory)
            if revision_path.name == 'code' and revision_path.parent.name == revision_name:
                # Get the sample directory (parent of revision<n>)
                sample_path = revision_path.parent.parent
                revision_dirs.append((revision_path, sample_path))
    
    total_copied = 0
    for revision_path, sample_path in revision_dirs:
        print(f"Copying files from: {revision_path}")
        print(f"To: {sample_path}/code/")
        
        # Create sample/code directory if it doesn't exist
        code_dest_path = sample_path / "code"
        code_dest_path.mkdir(parents=True, exist_ok=True)
        
        # Copy all files from revision0/code/ to sample<n>/code/
        copied_files = []
        for item in revision_path.iterdir():
            if item.is_file():
                dest_path = code_dest_path / item.name
                shutil.copy2(str(item), str(dest_path))
                copied_files.append(item.name)
                print(f"  Copied: {item.name}")
            elif item.is_dir():
                dest_path = code_dest_path / item.name
                # Remove destination if it exists to avoid conflicts
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                shutil.copytree(str(item), str(dest_path))
                copied_files.append(f"{item.name}/ (directory)")
                print(f"  Copied directory: {item.name}")
        
        print(f"  Total files/directories copied: {len(copied_files)}")
        print()
        total_copied += 1
    
    print(f"Copied files from {total_copied} revision directories")
    print()


def copy_model_directory_to_destination(model_name, destination_path, revision_num):
    """
    Copy the entire model directory to the destination and rename it to model_name_revision_n.
    
    Args:
        model_name: Model name
        destination_path: Destination path
        revision_num: Revision number for naming
    """
    destination_path = Path(destination_path)
    destination_path.mkdir(parents=True, exist_ok=True)
    
    # Look for the model directory in revision_results
    model_source_path = Path("revision_results") / model_name
    
    if not model_source_path.exists():
        print(f"Model directory not found: {model_source_path}")
        return False
    
    # Create new directory name: model_name_revision_n
    new_directory_name = f"{model_name}_revision_{revision_num}"
    final_destination = destination_path / new_directory_name
    
    print(f"Copying model directory from: {model_source_path}")
    print(f"To: {final_destination}")
    print(f"Renaming from '{model_name}' to '{new_directory_name}'")
    
    # If destination already exists, remove it first
    if final_destination.exists():
        print(f"  Destination exists, removing: {final_destination}")
        shutil.rmtree(final_destination)
    
    shutil.copytree(str(model_source_path), str(final_destination))
    print(f"  Successfully copied and renamed model directory")
    return True


def remove_revision_folders_in_destination(destination_model_path, revision_num):
    """
    Remove all revision folders in the destination, including the one we copied from.
    
    Args:
        destination_model_path: Path to the copied model directory
        revision_num: Revision number that was copied (will also be removed)
    """
    print(f"Removing all revision folders in destination: {destination_model_path}")
    
    # Walk through the directory structure and find all revision folders
    revision_folders_to_remove = []
    
    for root, dirs, files in os.walk(destination_model_path):
        for dir_name in dirs:
            if dir_name.startswith('revision'):
                revision_path = Path(root) / dir_name
                revision_folders_to_remove.append(revision_path)
    
    # Remove all revision folders (including the one we copied from)
    for revision_folder in revision_folders_to_remove:
        print(f"  Removing revision folder: {revision_folder}")
        shutil.rmtree(revision_folder)
    
    print(f"  Removed {len(revision_folders_to_remove)} revision folders")
    print()


def main():
    parser = argparse.ArgumentParser(description='Copy files from revision<n>/code/ to sample<m>/code/ and move model directory')
    parser.add_argument('model_name', help='Model name')
    parser.add_argument('destination_path', help='Destination path')
    parser.add_argument('--revision', type=int, default=0, help='Revision number to copy from (default: 0)')
    parser.add_argument('--sample', type=int, default=0, help='Sample number to copy to (default: 0)')
    
    args = parser.parse_args()
    
    model_name = args.model_name
    destination_path = args.destination_path
    revision_num = args.revision
    sample_num = args.sample
    
    print(f"Processing model: {model_name}")
    print(f"Destination: {destination_path}")
    print(f"Revision: {revision_num}")
    print(f"Sample: {sample_num}")
    print("=" * 60)
    
    # Step 1: Copy the entire model directory to destination
    print("Step 1: Copying model directory to destination")
    print("-" * 40)
    
    try:
        success = copy_model_directory_to_destination(model_name, destination_path, revision_num)
        if not success:
            print("Failed to copy model directory")
            sys.exit(1)
    except Exception as e:
        print(f"Error copying model directory: {e}")
        sys.exit(1)
    
    # Step 2: Copy files from revision<n>/code directories to sample<m>/code/ in destination
    print("Step 2: Copying files from revision<n>/code directories")
    print("-" * 40)
    
    destination_model_path = Path(destination_path) / f"{model_name}_revision_{revision_num}"
    if destination_model_path.exists():
        copy_files_from_revision_to_sample_in_destination(destination_model_path, revision_num, sample_num)
    else:
        print(f"Destination model path not found: {destination_model_path}")
        sys.exit(1)
    
    # Step 3: Remove all revision folders in destination
    print("Step 3: Removing all revision folders in destination")
    print("-" * 40)
    
    remove_revision_folders_in_destination(destination_model_path, revision_num)
    
    print("=" * 60)
    print(f"Successfully completed all operations for model '{model_name}'")
    print(f"Final directory name: '{model_name}_revision_{revision_num}'")


if __name__ == "__main__":
    main()
