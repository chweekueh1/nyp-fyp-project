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
    5. Newline normalization
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
        "```mermaid \\n\\n abc ```\\n\\n"

        >>> format_markdown("Some text\\n\\nMore text")
        "Some text\\n\\n\\nMore text"
    """
    if not text:
        return text

    # Step 1: Normalize newlines
    formatted_text = _normalize_newlines(text)

    # Step 2: Format and validate Mermaid blocks (includes sanitization)
    formatted_text = _format_and_validate_mermaid_blocks(formatted_text)

    # Step 3: Format markdown tables
    formatted_text = _format_markdown_tables(formatted_text)

    # Step 4: Format other code blocks with proper spacing
    formatted_text = _format_code_blocks(formatted_text)

    # Step 5: Escape arrow characters in non-code content (excluding Mermaid blocks)
    formatted_text = _escape_arrow_characters_except_mermaid(formatted_text)

    return formatted_text


def _normalize_newlines(text: str) -> str:
    """
    Normalize newline characters in the text.

    This function replaces two consecutive newline characters with three,
    ensuring proper markdown rendering spacing.

    :param text: Input text to normalize
    :type text: str
    :return: Text with normalized newlines
    :rtype: str
    """
    # Replace two newlines with three for proper markdown spacing
    return re.sub(r"\n\n", "\n\n\n", text)


def _format_and_validate_mermaid_blocks(text: str) -> str:
    """
    Format and validate Mermaid diagram blocks with comprehensive sanitization.

    This function processes Mermaid code blocks to ensure:
    1. Valid Mermaid syntax and directives
    2. HTML entity sanitization for safety
    3. Proper spacing for diagram rendering
    4. Error handling for malformed diagrams
    5. Consistent formatting for Gradio markdown rendering

    Common issues fixed:
    - Missing Mermaid directives (adds 'flowchart TD' if missing)
    - HTML special characters in node names/labels
    - Empty or malformed diagram blocks
    - Improper line endings
    - Insufficient spacing for Markdown rendering

    :param text: Input text containing Mermaid blocks
    :type text: str
    :return: Text with properly formatted and validated Mermaid blocks
    :rtype: str
    """
    # Pattern to match Mermaid blocks: ```mermaid ... ```
    mermaid_pattern = r"```mermaid\s*\n(.*?)\n```"

    def format_and_validate_mermaid_block(match) -> str:
        mermaid_content = match.group(1)

        # Comprehensive Mermaid syntax validation and sanitization
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

            # For Mermaid diagrams, we should NOT escape special characters
            # as they are essential for the diagram syntax
            # Only sanitize potentially dangerous HTML entities in node names/labels
            # but preserve all Mermaid syntax characters including arrows

            # Only escape HTML entities that could cause security issues in node names/labels
            # but NOT in the diagram syntax itself
            # Be more selective to avoid escaping > characters in arrow sequences

            # First, temporarily replace arrow sequences to protect them
            mermaid_content = mermaid_content.replace("-->", "ARROWLONGPLACEHOLDER")
            mermaid_content = mermaid_content.replace("->", "ARROWSHORTPLACEHOLDER")
            mermaid_content = mermaid_content.replace("-.->", "ARROWDOTTEDPLACEHOLDER")
            mermaid_content = mermaid_content.replace("==>", "ARROWTHICKPLACEHOLDER")
            mermaid_content = mermaid_content.replace("=>", "ARROWFATPLACEHOLDER")

            # Now escape HTML entities (excluding the protected arrow sequences)
            sanitized_content = re.sub(
                r'[<>"&]',
                lambda m: {"<": "&lt;", ">": "&gt;", '"': "&quot;", "&": "&amp;"}.get(
                    m.group(0), m.group(0)
                ),
                mermaid_content,
            )

            # Restore arrow sequences (they should remain unescaped)
            sanitized_content = sanitized_content.replace("ARROWLONGPLACEHOLDER", "-->")
            sanitized_content = sanitized_content.replace("ARROWSHORTPLACEHOLDER", "->")
            sanitized_content = sanitized_content.replace(
                "ARROWDOTTEDPLACEHOLDER", "-.->"
            )
            sanitized_content = sanitized_content.replace(
                "ARROWTHICKPLACEHOLDER", "==>"
            )
            sanitized_content = sanitized_content.replace("ARROWFATPLACEHOLDER", "=>")

            # DO NOT escape arrow characters in Mermaid diagrams
            # Arrows like ->, -->, -.->, ==> are essential for Mermaid syntax
            # and should be preserved exactly as they are

            # Enclose strings with double quotes for better readability
            sanitized_content = _enclose_strings_in_mermaid_diagrams(sanitized_content)

            # Ensure proper line endings
            sanitized_content = "\n".join(
                line.rstrip() for line in sanitized_content.split("\n")
            )

            # Add extra newlines for proper Markdown rendering
            # This ensures the Mermaid diagram is properly separated from surrounding text
            return f"\n\n```mermaid\n{sanitized_content}\n```\n\n"

        except Exception as e:
            logger.warning(f"Error sanitizing Mermaid syntax: {e}")
            # Return a safe fallback diagram with extra newlines
            return "\n\n```mermaid\nflowchart TD\n    A[Diagram Error]\n    B[Please try again]\n    A --> B\n```\n\n"

    # Replace all Mermaid blocks with validated and sanitized versions
    return re.sub(
        mermaid_pattern, format_and_validate_mermaid_block, text, flags=re.DOTALL
    )


def _enclose_strings_in_mermaid_diagrams(mermaid_content: str) -> str:
    """
    Enclose strings with double quotes in Mermaid diagrams for better readability and syntax clarity.

    This function processes Mermaid diagram content to:
    1. Identify node labels and text that should be enclosed in quotes
    2. Add double quotes around appropriate strings
    3. Preserve existing quoted strings
    4. Handle edge cases and special characters

    :param mermaid_content: The Mermaid diagram content to process
    :type mermaid_content: str
    :return: Mermaid content with strings properly enclosed in double quotes
    :rtype: str
    """
    if not mermaid_content:
        return mermaid_content

    lines = mermaid_content.split("\n")
    processed_lines = []

    for line in lines:
        # Skip empty lines and directive lines
        if not line.strip() or line.strip().startswith(
            (
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
            )
        ):
            processed_lines.append(line)
            continue

        # Process node definitions and edge labels
        processed_line = _process_mermaid_line(line)
        processed_lines.append(processed_line)

    return "\n".join(processed_lines)


def _process_mermaid_line(line: str) -> str:
    """
    Process a single line of Mermaid diagram content to enclose strings in quotes.

    :param line: A single line of Mermaid content
    :type line: str
    :return: Processed line with strings enclosed in quotes
    :rtype: str
    """
    # Skip lines that are already properly quoted or are directives
    if line.strip().startswith(
        (
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
        )
    ):
        return line

    # Handle node definitions: A[Label] or A["Label"] or A(Label) or A("Label")
    # Pattern: node_id[text] or node_id["text"] or node_id(text) or node_id("text")
    node_pattern = r'(\w+)\[([^"\]]*)\]'
    quoted_node_pattern = r'(\w+)\["([^"]*)"\]'

    # Check if line already has quoted nodes
    if re.search(quoted_node_pattern, line):
        # Already has quotes, just return as is
        return line

    # Process unquoted nodes
    def replace_node(match):
        node_id = match.group(1)
        label = match.group(2).strip()

        # Skip if label is empty or already contains special characters
        if not label or any(char in label for char in ["<", ">", "&", '"']):
            return match.group(0)

        # Enclose label in quotes
        return f'{node_id}["{label}"]'

    line = re.sub(node_pattern, replace_node, line)

    # Handle edge labels: A -->|label| B or A --> B
    # Pattern: -->|text| or -->|"text"|
    edge_label_pattern = r'-->\|([^"|]*)\|'
    quoted_edge_pattern = r'-->\|"([^"]*)"\|'

    # Check if edge already has quotes
    if re.search(quoted_edge_pattern, line):
        return line

    # Process unquoted edge labels
    def replace_edge_label(match):
        label = match.group(1).strip()

        # Skip if label is empty or contains special characters
        if not label or any(char in label for char in ["<", ">", "&", '"']):
            return match.group(0)

        # Enclose label in quotes
        return f'-->|"{label}"|'

    line = re.sub(edge_label_pattern, replace_edge_label, line)

    # Handle other arrow types with labels
    arrow_patterns = [
        (r'->\|([^"|]*)\|', r'->|"\1"|'),  # ->|label|
        (r'-\.->\|([^"|]*)\|', r'-.->|"\1"|'),  # -.->|label|
        (r'==>\|([^"|]*)\|', r'==>|"\1"|'),  # ==>|label|
        (r'=>\|([^"|]*)\|', r'=>|"\1"|'),  # =>|label|
    ]

    for pattern, replacement in arrow_patterns:
        quoted_pattern = pattern.replace(r'([^"|]*)\|', r'"([^"]*)"\|')
        if not re.search(quoted_pattern, line):
            line = re.sub(pattern, replacement, line)

    return line


def _format_code_blocks(text: str) -> str:
    """
    Format code blocks (excluding Mermaid) to ensure proper spacing and safety.

    This function processes all code blocks (```language ... ```) except Mermaid to:
    1. Ensure proper spacing before and after the block
    2. Handle newlines within the block content
    3. Add safety measures for potentially unsafe content

    :param text: Input text containing code blocks
    :type text: str
    :return: Text with properly formatted code blocks
    :rtype: str
    """
    # Pattern to match code blocks: ```language ... ``` (excluding mermaid)
    code_block_pattern = r"```(?!mermaid)(\w+)\s*\n(.*?)\n```"

    def format_code_block(match) -> str:
        language = match.group(1)
        content = match.group(2)

        # Normalize newlines within the content
        formatted_content = _normalize_newlines(content)

        # Ensure proper spacing around the code block
        return f"\n\n```{language}\n{formatted_content}\n```\n\n"

    return re.sub(code_block_pattern, format_code_block, text, flags=re.DOTALL)


def _escape_arrow_characters_except_mermaid(text: str) -> str:
    """
    Escape arrow characters in text except within Mermaid diagram blocks.

    This function handles common arrow sequences that might cause rendering issues
    in markdown or HTML contexts, but preserves them in Mermaid diagrams where
    they are essential for the syntax.

    :param text: The text to escape arrow characters in.
    :type text: str
    :return: Text with arrow characters escaped (except in Mermaid blocks).
    :rtype: str
    """
    if not text:
        return text

    # Pattern to match Mermaid blocks: ```mermaid ... ```
    mermaid_pattern = r"```mermaid\s*\n(.*?)\n```"

    def escape_non_mermaid_content(match) -> str:
        mermaid_block = match.group(0)  # Keep the entire Mermaid block unchanged
        return mermaid_block

        # First, temporarily replace Mermaid blocks with placeholders

    mermaid_blocks = []

    def store_mermaid_block(match) -> str:
        mermaid_blocks.append(match.group(0))
        return f"MERMAID_BLOCK_PLACEHOLDER_{len(mermaid_blocks) - 1}"

    # Replace Mermaid blocks with placeholders
    text_without_mermaid = re.sub(
        mermaid_pattern, store_mermaid_block, text, flags=re.DOTALL
    )

    # Now escape arrow characters in the non-Mermaid content
    # Use temporary placeholders to avoid conflicts with other escaping
    # Define arrow patterns to escape (longer patterns first)
    arrow_patterns = [
        ("-->", "ARROWLONGPLACEHOLDER"),  # Long arrow
        ("-.->", "ARROWDOTTEDPLACEHOLDER"),  # Dotted arrow
        ("==>", "ARROWTHICKPLACEHOLDER"),  # Thick arrow
        ("=>", "ARROWFATPLACEHOLDER"),  # Fat arrow
        ("->", "ARROWSHORTPLACEHOLDER"),  # Short arrow
    ]

    # Apply escaping in order (longer patterns first to avoid conflicts)
    for pattern, placeholder in arrow_patterns:
        text_without_mermaid = text_without_mermaid.replace(pattern, placeholder)

    # Restore placeholders with proper escaping
    text_without_mermaid = text_without_mermaid.replace(
        "ARROWLONGPLACEHOLDER", "\\-\\-\\>"
    )
    text_without_mermaid = text_without_mermaid.replace(
        "ARROWDOTTEDPLACEHOLDER", "\\-\\.\\-\\>"
    )
    text_without_mermaid = text_without_mermaid.replace(
        "ARROWTHICKPLACEHOLDER", "\\=\\=\\>"
    )
    text_without_mermaid = text_without_mermaid.replace("ARROWFATPLACEHOLDER", "\\=\\>")
    text_without_mermaid = text_without_mermaid.replace(
        "ARROWSHORTPLACEHOLDER", "\\-\\>"
    )

    # Restore Mermaid blocks (with their original, unescaped content)
    for i, mermaid_block in enumerate(mermaid_blocks):
        text_without_mermaid = text_without_mermaid.replace(
            f"MERMAID_BLOCK_PLACEHOLDER_{i}", mermaid_block
        )

    return text_without_mermaid


def _format_markdown_tables(text: str) -> str:
    """
    Format markdown tables to ensure proper alignment and spacing.

    This function processes markdown tables to:
    1. Ensure proper table structure
    2. Align columns correctly
    3. Add proper spacing around tables
    4. Validate table syntax
    5. Handle edge cases and malformed tables
    6. Escape special characters like | within cells

    :param text: Input text containing markdown tables
    :type text: str
    :return: Text with properly formatted markdown tables
    :rtype: str
    """
    if not text:
        return text

    # Pattern to match markdown tables
    # Matches: | header1 | header2 | header3 |
    #          |---------|---------|---------|
    #          | cell1   | cell2   | cell3   |
    table_pattern = r"(\|[^\n]*\|\n\|[-\s|:]+\|\n(?:\|[^\n]*\|\n?)*)"

    def escape_table_cell(cell: str) -> str:
        """Escape special characters in table cells."""
        # Escape special characters that can break markdown table formatting
        escaped = cell
        # Escape pipe characters that are not table separators
        escaped = escaped.replace("|", "\\|")
        # Escape backticks that can break markdown
        escaped = escaped.replace("`", "\\`")
        # Escape asterisks that can create unwanted emphasis
        escaped = escaped.replace("*", "\\*")
        # Escape underscores that can create unwanted emphasis
        escaped = escaped.replace("_", "\\_")
        # Escape square brackets that can create unwanted links
        escaped = escaped.replace("[", "\\[")
        escaped = escaped.replace("]", "\\]")
        # Escape parentheses that can create unwanted links
        escaped = escaped.replace("(", "\\(")
        escaped = escaped.replace(")", "\\)")
        # Escape hash symbols that can create unwanted headers
        escaped = escaped.replace("#", "\\#")
        # Escape plus signs that can create unwanted lists
        escaped = escaped.replace("+", "\\+")
        # Escape minus signs that can create unwanted lists
        escaped = escaped.replace("-", "\\-")
        # Escape exclamation marks that can create unwanted emphasis
        escaped = escaped.replace("!", "\\!")
        # Escape tilde that can create unwanted strikethrough
        escaped = escaped.replace("~", "\\~")
        return escaped

    def format_table(match) -> str:
        table_content = match.group(1)
        lines = table_content.strip().split("\n")

        if len(lines) < 2:
            return table_content  # Not a valid table

        # Process header row
        header_line = lines[0]
        separator_line = lines[1]

        # Ensure header starts and ends with |
        if not header_line.startswith("|"):
            header_line = "|" + header_line
        if not header_line.endswith("|"):
            header_line = header_line + "|"

        # Process separator line
        if not separator_line.startswith("|"):
            separator_line = "|" + separator_line
        if not separator_line.endswith("|"):
            separator_line = separator_line + "|"

        # Ensure separator has proper alignment markers
        separator_parts = separator_line.split("|")[
            1:-1
        ]  # Remove empty first/last parts
        formatted_separator_parts = []

        for part in separator_parts:
            part = part.strip()
            if part.startswith(":") and part.endswith(":"):
                # Center alignment
                formatted_separator_parts.append(":---:")
            elif part.endswith(":"):
                # Right alignment
                formatted_separator_parts.append("---:")
            elif part.startswith(":"):
                # Left alignment
                formatted_separator_parts.append(":---")
            else:
                # Default left alignment
                formatted_separator_parts.append("---")

        formatted_separator = "|" + "|".join(formatted_separator_parts) + "|"

        # Process data rows
        formatted_rows = []
        for line in lines[2:]:
            if line.strip():
                # Ensure row starts and ends with |
                if not line.startswith("|"):
                    line = "|" + line
                if not line.endswith("|"):
                    line = line + "|"

                # Clean up cell content and escape special characters
                cells = line.split("|")[1:-1]  # Remove empty first/last parts
                cleaned_cells = [escape_table_cell(cell.strip()) for cell in cells]
                formatted_rows.append("|" + "|".join(cleaned_cells) + "|")

        # Combine all parts
        formatted_table = f"{header_line}\n{formatted_separator}\n" + "\n".join(
            formatted_rows
        )

        # Add proper spacing around the table
        return f"\n\n{formatted_table}\n\n"

    return re.sub(table_pattern, format_table, text, flags=re.MULTILINE)


def _escape_arrow_characters(text: str) -> str:
    """
    Escape arrow characters in text to prevent them from being interpreted as HTML entities.

    This function handles common arrow sequences that might cause rendering issues
    in markdown or HTML contexts.

    :param text: The text to escape arrow characters in.
    :type text: str
    :return: Text with arrow characters escaped.
    :rtype: str
    """
    if not text:
        return text

    # Use temporary placeholders to avoid conflicts with other escaping
    # Define arrow patterns to escape (longer patterns first)
    arrow_patterns = [
        ("-->", "ARROWLONGPLACEHOLDER"),  # Long arrow
        ("-.->", "ARROWDOTTEDPLACEHOLDER"),  # Dotted arrow
        ("==>", "ARROWTHICKPLACEHOLDER"),  # Thick arrow
        ("=>", "ARROWFATPLACEHOLDER"),  # Fat arrow
        ("->", "ARROWSHORTPLACEHOLDER"),  # Short arrow
    ]

    # Apply escaping in order (longer patterns first to avoid conflicts)
    for pattern, placeholder in arrow_patterns:
        text = text.replace(pattern, placeholder)

    # Restore placeholders with proper escaping
    text = text.replace("ARROWLONGPLACEHOLDER", "\\-\\-\\>")
    text = text.replace("ARROWDOTTEDPLACEHOLDER", "\\-\\.\\-\\>")
    text = text.replace("ARROWTHICKPLACEHOLDER", "\\=\\=\\>")
    text = text.replace("ARROWFATPLACEHOLDER", "\\=\\>")
    text = text.replace("ARROWSHORTPLACEHOLDER", "\\-\\>")

    return text


def safe_markdown_format(text: str) -> str:
    """
    Safely format markdown text with additional safety measures.

    This function provides an additional layer of safety by:
    1. Sanitizing potentially dangerous content
    2. Ensuring proper markdown formatting
    3. Validating and sanitizing Mermaid diagrams

    :param text: The input markdown text to format safely
    :type text: str
    :return: Safely formatted markdown text
    :rtype: str

    :Example:
        >>> safe_markdown_format("```mermaid \\n abc ```")
        "```mermaid \\n\\n abc ```\\n\\n"
    """
    if not text:
        return text

    # Apply unified markdown formatting (includes Mermaid validation)
    return format_markdown(text)


# Legacy function for backward compatibility
def validate_and_sanitize_mermaid_syntax(text: str) -> str:
    """
    Legacy function for backward compatibility.

    This function is now deprecated and redirects to the unified format_markdown function.
    Use format_markdown() instead for all markdown processing.

    :param text: The text that may contain Mermaid diagrams
    :type text: str
    :return: Formatted text with validated Mermaid syntax
    :rtype: str
    """
    logger.warning(
        "validate_and_sanitize_mermaid_syntax is deprecated. Use format_markdown() instead."
    )
    return format_markdown(text)
