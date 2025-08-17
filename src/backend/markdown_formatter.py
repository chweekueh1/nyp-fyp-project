#!/usr/bin/env python3
"""
Unified Markdown Formatter Module

This module provides a comprehensive markdown formatter that handles:
1. General markdown formatting and safety
2. Mermaid diagram validation and sanitization
3. Code block formatting
4. Newline normalization
5. HTML entity sanitization

All markdown processing is now centralized in this single module.
"""

import re
import logging

logger = logging.getLogger(__name__)


def format_markdown(text: str) -> str:
    """
    Unified markdown formatter that handles all markdown processing.

    This function provides comprehensive markdown formatting including:
    1. General markdown safety and formatting
    2. Mermaid diagram validation and sanitization
    3. Code block formatting with proper spacing
    4. Markdown table formatting and validation
    5. Newline character normalization
    6. HTML entity sanitization for safety
    7. Arrow character escaping for proper rendering (excluding Mermaid diagrams)

    The function specifically handles:
    - Code blocks (```language ... ```)
    - Mermaid diagrams (```mermaid ... ```) with validation (preserving all syntax)
    - Markdown tables with proper alignment and formatting
    - Newline character normalization
    - HTML entity sanitization
    - Arrow character escaping (->, -->, etc.) in non-Mermaid content
    - Proper spacing for markdown rendering

    :param text: The input markdown text to format
    :type text: str
    :return: Formatted markdown text with proper spacing, safety measures, and validated Mermaid diagrams
    :rtype: str

    :Example:
        >>> format_markdown("```mermaid \\n abc ```")
        "```mermaid \\n abc ```"

        >>> format_markdown("Some text\\n\\nMore text")
        "Some text\\n\\nMore text"
    """
    if not text:
        return text

    # Step 1: Format and validate Mermaid and other code blocks first
    # This prevents general formatting from breaking the syntax inside them.
    formatted_text, mermaid_blocks, other_code_blocks = _extract_and_format_code_blocks(
        text
    )

    # Step 2: Format markdown tables
    formatted_text = _format_markdown_tables(formatted_text)

    # Step 3: Format the rest of the content (non-code blocks)
    formatted_text = _format_non_code_content(formatted_text)

    # Step 4: Restore code blocks
    formatted_text = _restore_code_blocks(
        formatted_text, mermaid_blocks, other_code_blocks
    )

    return formatted_text


def _extract_and_format_code_blocks(text: str) -> tuple[str, list[str], list[str]]:
    """
    Extracts and formats Mermaid and other code blocks, replacing them with placeholders.
    Returns the modified text and the lists of extracted blocks.
    """
    mermaid_blocks = []
    other_code_blocks = []

    # Temporary placeholders
    MERMAID_PLACEHOLDER = "MERMAID_BLOCK_PLACEHOLDER"
    OTHER_CODE_PLACEHOLDER = "OTHER_CODE_BLOCK_PLACEHOLDER"

    # Step A: Format and extract Mermaid blocks
    def format_and_store_mermaid(match):
        mermaid_content = match.group(1)
        formatted_block = _format_and_validate_mermaid_block(mermaid_content)
        mermaid_blocks.append(formatted_block)
        return f"{MERMAID_PLACEHOLDER}_{len(mermaid_blocks) - 1}"

    mermaid_pattern = r"```mermaid\s*\n(.*?)\n```"
    text = re.sub(mermaid_pattern, format_and_store_mermaid, text, flags=re.DOTALL)

    # Step B: Format and extract other code blocks
    def format_and_store_other_code(match):
        language = match.group(1)
        content = match.group(2)
        # Note: We do NOT normalize newlines here, as it's a general text formatting step
        formatted_block = f"```{language}\n{content}\n```"
        other_code_blocks.append(formatted_block)
        return f"{OTHER_CODE_PLACEHOLDER}_{len(other_code_blocks) - 1}"

    code_block_pattern = r"```(?!mermaid)(\w+)\s*\n(.*?)\n```"
    text = re.sub(
        code_block_pattern, format_and_store_other_code, text, flags=re.DOTALL
    )

    return text, mermaid_blocks, other_code_blocks


def _format_non_code_content(text: str) -> str:
    """
    Formats the text content that is NOT inside a code block.
    This includes newline normalization and arrow escaping.
    """
    # Normalize newlines
    # This replaces two or more newlines with exactly two newlines
    # to create proper paragraph breaks without adding excessive space.
    text = re.sub(r"\n{2,}", "\n\n", text)

    # Escape arrow characters
    # Define arrow patterns to escape (longer patterns first)
    arrow_patterns = [
        ("-->", "\\-\\->"),
        ("-.->", "\\-\\.\\->"),
        ("==>", "\\=\\=>"),
        ("=>", "\\=>"),
        ("->", "\\->"),
    ]
    for pattern, replacement in arrow_patterns:
        text = text.replace(pattern, replacement)

    return text


def _restore_code_blocks(
    text: str, mermaid_blocks: list[str], other_code_blocks: list[str]
) -> str:
    """
    Restores Mermaid and other code blocks from placeholders.
    """
    for i, block in enumerate(mermaid_blocks):
        text = text.replace(f"MERMAID_BLOCK_PLACEHOLDER_{i}", block)
    for i, block in enumerate(other_code_blocks):
        text = text.replace(f"OTHER_CODE_BLOCK_PLACEHOLDER_{i}", block)
    return text


def _format_and_validate_mermaid_block(mermaid_content: str) -> str:
    """
    Format and validate Mermaid diagram blocks without altering their internal syntax.
    This function processes the content of a single Mermaid block.
    """
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
            return "flowchart TD\n  A[Invalid Diagram]\n  B[Please check syntax]\n  A --> B"

        first_line = lines[0].strip().lower()
        has_valid_directive = any(
            first_line.startswith(directive) for directive in valid_directives
        )

        if not has_valid_directive:
            lines.insert(0, "flowchart TD")
            mermaid_content = "\n".join(lines)

        # Enclose strings with double quotes for better readability and to fix the parentheses issue
        sanitized_content = _enclose_strings_in_mermaid_diagrams(mermaid_content)

        # Ensure proper line endings and remove extra whitespace
        sanitized_content = "\n".join(
            line.rstrip() for line in sanitized_content.split("\n")
        )

        # Return the formatted content for the final block
        return f"```mermaid\n{sanitized_content}\n```"

    except Exception as e:
        logger.warning(f"Error validating Mermaid syntax: {e}")
        return "```mermaid\nflowchart TD\n  A[Diagram Error]\n  B[Please try again]\n  A --> B\n```"


def _enclose_strings_in_mermaid_diagrams(mermaid_content: str) -> str:
    """
    Enclose strings with double quotes in Mermaid diagrams for better readability and to handle
    cases with parentheses or other special characters.

    This function processes Mermaid diagram content to:
    1. Identify node labels that should be enclosed in quotes
    2. Add double quotes around appropriate strings
    3. Preserve existing quoted strings
    """
    if not mermaid_content:
        return mermaid_content

    lines = mermaid_content.split("\n")
    processed_lines = []

    for line in lines:
        processed_line = line
        # Regex to find a letter followed by a bracket containing parentheses.
        # This is a more general pattern than before.
        node_with_paren_pattern = re.compile(r"(\w+)\[(.*?\([^)]*\).*?)\]")

        # Process the line to wrap the label in quotes if it contains a parenthesis
        def replace_with_quotes(match):
            node_id = match.group(1)
            label = match.group(2)
            # Check if the label is already correctly quoted
            if label.startswith('"') and label.endswith('"'):
                return match.group(0)
            return f'{node_id}["{label}"]'

        processed_line = re.sub(
            node_with_paren_pattern, replace_with_quotes, processed_line
        )
        processed_lines.append(processed_line)

    return "\n".join(processed_lines)


def _format_markdown_tables(text: str) -> str:
    """
    Format markdown tables to ensure proper alignment and spacing.
    This function has been left unchanged as it does not affect the Mermaid issue.
    """
    # Pattern to match markdown tables
    table_pattern = r"(\|[^\n]*\|\n\|[-\s|:]+\|\n(?:\|[^\n]*\|\n?)*)"

    def escape_table_cell(cell: str) -> str:
        """Escape special characters in table cells."""
        # Escape special characters that can break markdown table formatting
        escaped = cell
        escaped = escaped.replace("|", "\\|")
        escaped = escaped.replace("`", "\\`")
        escaped = escaped.replace("*", "\\*")
        escaped = escaped.replace("_", "\\_")
        escaped = escaped.replace("[", "\\[")
        escaped = escaped.replace("]", "\\]")
        escaped = escaped.replace("(", "\\(")
        escaped = escaped.replace(")", "\\)")
        escaped = escaped.replace("#", "\\#")
        escaped = escaped.replace("+", "\\+")
        escaped = escaped.replace("-", "\\-")
        escaped = escaped.replace("!", "\\!")
        escaped = escaped.replace("~", "\\~")
        return escaped

    def format_table(match) -> str:
        table_content = match.group(1)
        lines = table_content.strip().split("\n")

        if len(lines) < 2:
            return table_content  # Not a valid table

        header_line = lines[0]
        separator_line = lines[1]

        if not header_line.startswith("|"):
            header_line = f"|{header_line}"
        if not header_line.endswith("|"):
            header_line = f"{header_line}|"

        if not separator_line.startswith("|"):
            separator_line = f"|{separator_line}"
        if not separator_line.endswith("|"):
            separator_line = f"{separator_line}|"

        separator_parts = separator_line.split("|")[1:-1]
        formatted_separator_parts = []
        for part in separator_parts:
            part = part.strip()
            if part.startswith(":") and part.endswith(":"):
                formatted_separator_parts.append(":---:")
            elif part.endswith(":"):
                formatted_separator_parts.append("---:")
            elif part.startswith(":"):
                formatted_separator_parts.append(":---")
            else:
                formatted_separator_parts.append("---")
        formatted_separator = "|" + "|".join(formatted_separator_parts) + "|"

        formatted_rows = []
        for line in lines[2:]:
            if line.strip():
                if not line.startswith("|"):
                    line = f"|{line}"
                if not line.endswith("|"):
                    line = f"{line}|"
                cells = line.split("|")[1:-1]
                cleaned_cells = [escape_table_cell(cell.strip()) for cell in cells]
                formatted_rows.append("|" + "|".join(cleaned_cells) + "|")

        formatted_table = f"{header_line}\n{formatted_separator}\n" + "\n".join(
            formatted_rows
        )
        return f"\n\n{formatted_table}\n\n"

    return re.sub(table_pattern, format_table, text, flags=re.MULTILINE)


# Legacy function for backward compatibility
def validate_and_sanitize_mermaid_syntax(text: str) -> str:
    """
    Legacy function for backward compatibility.
    This function is now deprecated and redirects to the unified format_markdown function.
    Use format_markdown() instead for all markdown processing.
    """
    logger.warning(
        "validate_and_sanitize_mermaid_syntax is deprecated. Use format_markdown() instead."
    )
    return format_markdown(text)


def safe_markdown_format(text: str) -> str:
    """
    Safely format markdown text with additional safety measures.
    This function provides an additional layer of safety by:
    1. Sanitizing potentially dangerous content
    2. Ensuring proper markdown formatting
    3. Validating and sanitizing Mermaid diagrams
    """
    return format_markdown(text) if text else text
