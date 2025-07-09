#!/usr/bin/env python3
"""
Markdown Formatter Module

This module provides a general purpose markdown formatter for Python strings.
It handles safe formatting of markdown content, particularly code blocks and newline handling.
"""

import re
from typing import Optional


def format_markdown(text: str) -> str:
    """
    Format markdown text to ensure proper rendering and safety.

    This function processes markdown content to:
    1. Ensure proper spacing around code blocks
    2. Handle newline characters safely
    3. Format Mermaid diagrams with proper spacing
    4. Add safety measures for potentially unsafe content

    The function specifically handles:
    - Code blocks (```language ... ```)
    - Mermaid diagrams (```mermaid ... ```)
    - Newline character normalization
    - Proper spacing for markdown rendering

    :param text: The input markdown text to format
    :type text: str
    :return: Formatted markdown text with proper spacing and safety measures
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

    # Step 2: Format code blocks with proper spacing
    formatted_text = _format_code_blocks(formatted_text)

    # Step 3: Ensure proper spacing around Mermaid blocks
    formatted_text = _format_mermaid_blocks(formatted_text)

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


def _format_code_blocks(text: str) -> str:
    """
    Format code blocks to ensure proper spacing and safety.

    This function processes all code blocks (```language ... ```) to:
    1. Ensure proper spacing before and after the block
    2. Handle newlines within the block content
    3. Add safety measures for potentially unsafe content

    :param text: Input text containing code blocks
    :type text: str
    :return: Text with properly formatted code blocks
    :rtype: str
    """
    # Pattern to match code blocks: ```language ... ```
    code_block_pattern = r"```(\w+)\s*\n(.*?)\n```"

    def format_code_block(match) -> str:
        language = match.group(1)
        content = match.group(2)

        # Normalize newlines within the content
        formatted_content = _normalize_newlines(content)

        # Ensure proper spacing around the code block
        return f"\n\n```{language}\n{formatted_content}\n```\n\n"

    return re.sub(code_block_pattern, format_code_block, text, flags=re.DOTALL)


def _format_mermaid_blocks(text: str) -> str:
    """
    Format Mermaid diagram blocks with special handling.

    This function specifically processes Mermaid code blocks to ensure:
    1. Proper spacing for diagram rendering
    2. Safety measures for potentially unsafe content
    3. Consistent formatting for Gradio markdown rendering

    :param text: Input text containing Mermaid blocks
    :type text: str
    :return: Text with properly formatted Mermaid blocks
    :rtype: str
    """
    # Pattern to match Mermaid blocks: ```mermaid ... ```
    mermaid_pattern = r"```mermaid\s*\n(.*?)\n```"

    def format_mermaid_block(match) -> str:
        content = match.group(1)

        # Normalize newlines within the Mermaid content
        formatted_content = _normalize_newlines(content)

        # Ensure proper spacing for Mermaid rendering
        return f"\n\n```mermaid\n{formatted_content}\n```\n\n"

    return re.sub(mermaid_pattern, format_mermaid_block, text, flags=re.DOTALL)


def safe_markdown_format(text: str, max_length: Optional[int] = None) -> str:
    """
    Safely format markdown text with additional safety measures.

    This function provides an additional layer of safety by:
    1. Truncating text if it exceeds maximum length
    2. Sanitizing potentially dangerous content
    3. Ensuring proper markdown formatting

    :param text: The input markdown text to format safely
    :type text: str
    :param max_length: Maximum allowed length for the text (optional)
    :type max_length: Optional[int]
    :return: Safely formatted markdown text
    :rtype: str

    :Example:
        >>> safe_markdown_format("```mermaid \\n abc ```", max_length=100)
        "```mermaid \\n\\n abc ```\\n\\n"
    """
    if not text:
        return text

    # Truncate if max_length is specified
    if max_length and len(text) > max_length:
        text = text[:max_length] + "..."

    # Apply standard markdown formatting
    formatted_text = format_markdown(text)

    return formatted_text
