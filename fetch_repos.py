#!/usr/bin/env python3
"""
Fetch dependencies using Git submodules.

This script is a wrapper around git submodule commands for convenience.
The actual dependencies are managed as Git submodules defined in .gitmodules.
"""

import subprocess
import sys


def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result.returncode == 0


def main():
    """Initialize and update Git submodules."""
    print("Initializing Git submodules...")
    
    # Initialize submodules
    if not run_command(["git", "submodule", "update", "--init", "--recursive"]):
        print("Error: Failed to initialize submodules", file=sys.stderr)
        sys.exit(1)
    
    print("\n✅ All submodules initialized successfully!")
    print("\nNote: Dependencies are now managed as Git submodules.")
    print("To update submodules to latest commits on their branches:")
    print("  git submodule update --remote")


if __name__ == "__main__":
    main()
