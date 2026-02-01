#!/usr/bin/env python3
"""
Simplified test for reading MD files.
Tests: Can we read all MD files? Were any modified? Basic statistics.
"""

import os
import hashlib
import glob
from pathlib import Path


def compute_checksum(filepath):
    """Compute MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def list_md_files(root_dir):
    """List all MD files in the project."""
    pattern = os.path.join(root_dir, "**", "*.md")
    return glob.glob(pattern, recursive=True)


def read_file(filepath):
    """Read a file using Python's open() function."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def main():
    """Main test function."""
    print("=" * 60)
    print("SIMPLE MD FILE READ TEST")
    print("=" * 60)
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir
    
    print(f"\nProject root: {project_root}")
    print("-" * 60)
    
    # Step 1: List all MD files
    print("\n[STEP 1] Listing all MD files...")
    md_files = list_md_files(project_root)
    print(f"  Found {len(md_files)} MD files")
    
    if not md_files:
        print("  ERROR: No MD files found!")
        return False
    
    # Step 2: Compute checksums before reading
    print("\n[STEP 2] Computing checksums before reading...")
    checksums_before = {}
    for filepath in md_files:
        checksums_before[filepath] = compute_checksum(filepath)
    print(f"  Computed {len(checksums_before)} checksums")
    
    # Step 3: Read all files using Python's open()
    print("\n[STEP 3] Reading all MD files with open()...")
    files_read = 0
    total_bytes = 0
    errors = []
    
    for filepath in md_files:
        try:
            content = read_file(filepath)
            files_read += 1
            total_bytes += len(content.encode('utf-8'))
        except Exception as e:
            errors.append((filepath, str(e)))
    
    print(f"  Successfully read {files_read}/{len(md_files)} files")
    print(f"  Total content size: {total_bytes:,} bytes")
    
    if errors:
        print(f"  ERRORS: {len(errors)} files failed to read")
        for filepath, error in errors[:5]:
            print(f"    - {filepath}: {error}")
    
    # Step 4: Compute checksums after reading
    print("\n[STEP 4] Computing checksums after reading...")
    checksums_after = {}
    for filepath in md_files:
        checksums_after[filepath] = compute_checksum(filepath)
    print(f"  Computed {len(checksums_after)} checksums")
    
    # Step 5: Verify no files were modified
    print("\n[STEP 5] Verifying no files were modified...")
    modified_files = []
    for filepath in md_files:
        if checksums_before[filepath] != checksums_after[filepath]:
            modified_files.append(filepath)
    
    if modified_files:
        print(f"  WARNING: {len(modified_files)} files were modified!")
        for filepath in modified_files[:5]:
            print(f"    - {filepath}")
    else:
        print(f"  OK: No files were modified")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"  Total MD files found:     {len(md_files)}")
    print(f"  Files successfully read:  {files_read}")
    print(f"  Files with read errors:   {len(errors)}")
    print(f"  Files modified:           {len(modified_files)}")
    print(f"  Total bytes read:         {total_bytes:,}")
    
    # Determine success
    success = (
        files_read == len(md_files) and
        len(errors) == 0 and
        len(modified_files) == 0
    )
    
    print("-" * 60)
    if success:
        print("  RESULT: SUCCESS")
        print("  All MD files were read successfully without modifications")
    else:
        print("  RESULT: FAILURE")
        if files_read != len(md_files):
            print(f"  - Only {files_read}/{len(md_files)} files were read")
        if errors:
            print(f"  - {len(errors)} files had read errors")
        if modified_files:
            print(f"  - {len(modified_files)} files were unexpectedly modified")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
