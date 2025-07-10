#!/usr/bin/env python3
"""
Standalone test script to validate Mermaid syntax formatting.
This file has been moved from the root directory to tests/backend/ for better organization.
Updated to use the unified markdown formatter.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from backend.markdown_formatter import format_markdown


# Test cases
test_cases = [
    "Here is a diagram:\n```mermaid\ngraph TD\n    A --> B\n```\nAnd some text after.",
    "```mermaid\ngraph TD\n    A --> B\n```",
    "Text before\n```mermaid\ngraph TD\n    A --> B\n```\nText after",
    "```mermaid\ngraph TD\n    A --> B\n```\n```mermaid\nflowchart LR\n    C --> D\n```",
    "No mermaid here, just text.",
    "```mermaid\nA --> B\n```",  # Missing directive
    "```mermaid\n\n```",  # Empty diagram
]


def test_mermaid_validation():
    """Test Mermaid validation function with various inputs."""
    print("Testing Mermaid validation function...")
    print("=" * 50)

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Input: {repr(test)}")
        result = format_markdown(test)
        print(f"Output: {repr(result)}")

        # Check if we have proper newlines
        if "```mermaid" in result:
            # Count newlines before and after mermaid blocks
            lines = result.split("\n")
            mermaid_indices = [
                i for i, line in enumerate(lines) if "```mermaid" in line
            ]

            for idx in mermaid_indices:
                # Check newlines before
                newlines_before = 0
                for j in range(idx - 1, -1, -1):
                    if lines[j].strip() == "":
                        newlines_before += 1
                    else:
                        break

                # Check newlines after (find closing ```)
                closing_idx = None
                for j in range(idx + 1, len(lines)):
                    if "```" in lines[j] and "mermaid" not in lines[j]:
                        closing_idx = j
                        break

                newlines_after = 0
                if closing_idx:
                    for j in range(closing_idx + 1, len(lines)):
                        if lines[j].strip() == "":
                            newlines_after += 1
                        else:
                            break

                print(
                    f"  Mermaid block at line {idx}: {newlines_before} newlines before, {newlines_after} newlines after"
                )

        print("-" * 30)


if __name__ == "__main__":
    test_mermaid_validation()
