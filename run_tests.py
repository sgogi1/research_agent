#!/usr/bin/env python3
"""Test runner script for the research agent."""
import sys
import subprocess
from pathlib import Path

def main():
    """Run pytest with appropriate configuration."""
    project_root = Path(__file__).parent
    
    # Run pytest
    cmd = [
        sys.executable, "-m", "pytest",
        str(project_root / "tests"),
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-exclude=tests/*",
        "--cov-exclude=__pycache__/*"
    ]
    
    # Add markers if specified
    if len(sys.argv) > 1:
        if sys.argv[1] == "--unit":
            cmd.extend(["-m", "unit"])
        elif sys.argv[1] == "--integration":
            cmd.extend(["-m", "integration"])
        elif sys.argv[1] == "--system":
            cmd.extend(["-m", "system"])
        elif sys.argv[1] == "--all":
            pass  # Run all tests
        else:
            cmd.extend(sys.argv[1:])
    
    result = subprocess.run(cmd, cwd=project_root)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()

