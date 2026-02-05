#!/usr/bin/env python3
"""
Reorganize TaskX from flat src/ to proper src/taskx/ package structure.
Part of TASK_PACKET_TASKX_A0.
"""
import os
import shutil
from pathlib import Path

def main():
    repo_root = Path("/Users/hue/code/taskX")
    src = repo_root / "src"
    taskx_pkg = src / "taskx"
    
    # Create src/taskx if it doesn't exist
    taskx_pkg.mkdir(exist_ok=True)
    print(f"✓ Created {taskx_pkg}")
    
    # Move top-level Python files into src/taskx/
    files_to_move = [
        "__init__.py",
        "__main__.py", 
        "cli.py",
        "doctor.py",
        "ci_gate.py",
    ]
    
    for fname in files_to_move:
        src_file = src / fname
        dest_file = taskx_pkg / fname
        if src_file.exists() and not dest_file.exists():
            shutil.move(str(src_file), str(dest_file))
            print(f"✓ Moved {fname} → taskx/{fname}")
        elif dest_file.exists():
            print(f"  Skip {fname} (already exists in taskx/)")
        else:
            print(f"⚠ Skip {fname} (not found)")
    
    # Move subdirectories into src/taskx/
    dirs_to_move = ["utils", "schemas", "pipeline"]
    
    for dirname in dirs_to_move:
        src_dir = src / dirname
        dest_dir = taskx_pkg / dirname
        if src_dir.exists() and not dest_dir.exists():
            shutil.move(str(src_dir), str(dest_dir))
            print(f"✓ Moved {dirname}/ → taskx/{dirname}/")
        elif dest_dir.exists():
            print(f"  Skip {dirname}/ (already exists in taskx/)")
        else:
            print(f"⚠ Skip {dirname}/ (not found)")
    
    # taskx_adapters stays as separate package (already correctly namespaced)
    print("\n✓ taskx_adapters remains at src/taskx_adapters/")
    
    print("\n✓ Package restructure complete")
    print(f"\nNew structure:")
    for root, dirs, files in os.walk(taskx_pkg):
        level = root.replace(str(taskx_pkg), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in sorted(files)[:5]:  # Show first 5 files per dir
            print(f'{subindent}{file}')
        if len(files) > 5:
            print(f'{subindent}... and {len(files) - 5} more')

if __name__ == "__main__":
    main()
