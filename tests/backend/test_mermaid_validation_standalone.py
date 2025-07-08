#!/usr/bin/env python3
"""
Standalone test script to validate Mermaid syntax formatting.
This file has been moved from the root directory to tests/backend/ for better organization.
"""

import re


def validate_and_sanitize_mermaid_syntax(text):
    """
    Validates and sanitizes Mermaid syntax in text to prevent rendering errors.
    """
    if not text:
        return text

    # Pattern to match Mermaid code blocks
    mermaid_pattern = r"```mermaid\s*\n(.*?)\n```"

    def sanitize_mermaid_block(match):
        mermaid_content = match.group(1)

        # Basic Mermaid syntax validation and sanitization
        try:
            # Check if it starts with a valid Mermaid directive
            valid_directives = [
                "graph",
                "flowchart",
                "sequenceDiagram",
                "classDiagram",
                "gantt",
                "pie",
                "mindmap",
                "erDiagram",
                "journey",
                "gitgraph",
            ]

            lines = mermaid_content.strip().split("\n")
            if not lines:
                # Add extra newlines for proper Markdown rendering
                return "\n\n```mermaid\nflowchart TD\n    A[Invalid Diagram]\n    B[Please check syntax]\n    A --> B\n```\n\n"

            first_line = lines[0].strip().lower()
            has_valid_directive = any(
                first_line.startswith(directive) for directive in valid_directives
            )

            if not has_valid_directive:
                # Add a valid directive if missing
                lines.insert(0, "flowchart TD")
                mermaid_content = "\n".join(lines)

            # Sanitize special characters that might cause issues
            sanitized_content = re.sub(
                r'[<>"&]',
                lambda m: {"<": "&lt;", ">": "&gt;", '"': "&quot;", "&": "&amp;"}.get(
                    m.group(0), m.group(0)
                ),
                mermaid_content,
            )

            # Ensure proper line endings
            sanitized_content = "\n".join(
                line.rstrip() for line in sanitized_content.split("\n")
            )

            # Add extra newlines for proper Markdown rendering
            return f"\n\n```mermaid\n{sanitized_content}\n```\n\n"

        except Exception:
            # Return a safe fallback diagram with extra newlines
            return "\n\n```mermaid\nflowchart TD\n    A[Diagram Error]\n    B[Please try again]\n    A --> B\n```\n\n"

    # Replace all Mermaid blocks with sanitized versions
    sanitized_text = re.sub(
        mermaid_pattern, sanitize_mermaid_block, text, flags=re.DOTALL
    )

    return sanitized_text


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
        result = validate_and_sanitize_mermaid_syntax(test)
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
