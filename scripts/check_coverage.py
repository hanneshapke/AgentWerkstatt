#!/usr/bin/env python3
"""
Simple script to check test coverage and display results.
Can be used for local development to quickly check coverage status.
"""

import subprocess
import sys
import re
from pathlib import Path


def run_coverage():
    """Run pytest with coverage and return the total percentage."""
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "--cov=src/agentwerkstatt", "--cov-report=term-missing"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        if result.returncode != 0:
            print(f"❌ Tests failed with return code {result.returncode}")
            print("STDERR:", result.stderr)
            return None

        # Extract total coverage percentage
        total_match = re.search(r"TOTAL.*?(\d+)%", result.stdout)
        if total_match:
            coverage = int(total_match.group(1))
            print(f"📊 Current test coverage: {coverage}%")

            # Provide status emoji based on coverage
            if coverage >= 90:
                print("✅ Excellent coverage!")
            elif coverage >= 80:
                print("👍 Good coverage")
            elif coverage >= 70:
                print("⚠️  Coverage could be improved")
            else:
                print("❌ Coverage needs significant improvement")

            return coverage
        else:
            print("❌ Could not parse coverage percentage")
            return None

    except FileNotFoundError:
        print("❌ Error: 'uv' command not found. Please install uv first.")
        return None
    except Exception as e:
        print(f"❌ Error running coverage: {e}")
        return None


def main():
    print("🔍 Checking test coverage...\n")
    coverage = run_coverage()

    if coverage is not None:
        print(f"\n📈 Coverage badge will show: {coverage}%")
        print(
            "🔗 View detailed coverage report at: https://codecov.io/gh/hanneshapke/AgentWerkstatt"
        )
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
