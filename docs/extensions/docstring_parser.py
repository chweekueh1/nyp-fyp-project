#!/usr/bin/env python3
"""
Custom Sphinx extension for enhanced docstring parsing.

This extension provides improved support for both Google and Sphinx style docstrings,
and ensures that doc comments are properly processed.
"""

import re
from typing import Any, Dict, List, Optional

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.ext.autodoc import ModuleDocumenter, FunctionDocumenter, ClassDocumenter
from sphinx.ext.napoleon import GoogleDocstring, NumpyDocstring


class EnhancedGoogleDocstring(GoogleDocstring):
    """Enhanced Google-style docstring parser with better comment support."""

    def __init__(
        self,
        docstring: str,
        config: Optional[Dict[str, Any]] = None,
        what: str = "",
        name: str = "",
        obj: Any = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(docstring, config, what, name, obj, options)
        self._parse_doc_comments()

    def _parse_doc_comments(self) -> None:
        """Parse doc comments and integrate them into the docstring."""
        if not self._docstring:
            return

        # Look for doc comments (lines starting with #)
        lines = self._docstring.split("\n")
        processed_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                # Convert doc comment to regular docstring line
                comment_content = stripped[1:].strip()
                if comment_content:
                    processed_lines.append(comment_content)
            else:
                processed_lines.append(line)

        if processed_lines != lines:
            self._docstring = "\n".join(processed_lines)


class EnhancedNumpyDocstring(NumpyDocstring):
    """Enhanced NumPy-style docstring parser with better comment support."""

    def __init__(
        self,
        docstring: str,
        config: Optional[Dict[str, Any]] = None,
        what: str = "",
        name: str = "",
        obj: Any = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(docstring, config, what, name, obj, options)
        self._parse_doc_comments()

    def _parse_doc_comments(self) -> None:
        """Parse doc comments and integrate them into the docstring."""
        if not self._docstring:
            return

        # Look for doc comments (lines starting with #)
        lines = self._docstring.split("\n")
        processed_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                # Convert doc comment to regular docstring line
                comment_content = stripped[1:].strip()
                if comment_content:
                    processed_lines.append(comment_content)
            else:
                processed_lines.append(line)

        if processed_lines != lines:
            self._docstring = "\n".join(processed_lines)


class EnhancedModuleDocumenter(ModuleDocumenter):
    """Enhanced module documenter with better docstring parsing."""

    def get_doc(self) -> Optional[List[List[str]]]:
        """Get the docstring of the object."""
        docstring = super().get_doc()
        if docstring:
            # Process doc comments in module docstrings
            processed_docstring = self._process_doc_comments(docstring)
            return processed_docstring
        return docstring

    def _process_doc_comments(self, docstring: List[List[str]]) -> List[List[str]]:
        """Process doc comments in the docstring."""
        processed = []
        for section in docstring:
            processed_section = []
            for line in section:
                stripped = line.strip()
                if stripped.startswith("#"):
                    # Convert doc comment to regular docstring line
                    comment_content = stripped[1:].strip()
                    if comment_content:
                        processed_section.append(comment_content)
                else:
                    processed_section.append(line)
            processed.append(processed_section)
        return processed

    def add_content(self, more_content: Optional[List[nodes.Node]]) -> None:
        """Add content from docstrings, autodoc and user."""
        # Enhanced content processing for all modules
        if hasattr(self, "doc_as_astree") and self.doc_as_astree:
            # Process docstring as AST for better parsing
            self._process_enhanced_patterns()

        super().add_content(more_content)

    def _process_enhanced_patterns(self) -> None:
        """Process enhanced patterns in docstrings for all modules."""
        if not self.docstring:
            return

        # Look for common patterns and enhance them
        docstring = str(self.docstring)

        # Enhance common patterns across all modules
        patterns = [
            # Function and class definitions
            (r"def (\w+)\s*\(", r"Function: \1"),
            (r"class (\w+)", r"Class: \1"),
            (r"@(\w+)", r"Decorator: \1"),
            # Common library references
            (r"gradio\.(\w+)", r"Gradio \1 component"),
            (r"openai\.(\w+)", r"OpenAI \1"),
            (r"torch\.(\w+)", r"PyTorch \1"),
            (r"tensorflow\.(\w+)", r"TensorFlow \1"),
            (r"sklearn\.(\w+)", r"Scikit-learn \1"),
            (r"numpy\.(\w+)", r"NumPy \1"),
            (r"pandas\.(\w+)", r"Pandas \1"),
            # Google-style docstring sections
            (r"Args?:", "**Arguments:**"),
            (r"Returns?:", "**Returns:**"),
            (r"Raises?:", "**Raises:**"),
            (r"Yields?:", "**Yields:**"),
            (r"Example:", "**Example:**"),
            (r"Examples:", "**Examples:**"),
            (r"Note:", "**Note:**"),
            (r"Warning:", "**Warning:**"),
        ]

        for pattern, replacement in patterns:
            docstring = re.sub(pattern, replacement, docstring)

        # Update the docstring if changes were made
        if docstring != str(self.docstring):
            self.docstring = docstring


class EnhancedFunctionDocumenter(FunctionDocumenter):
    """Enhanced function documenter with better docstring parsing."""

    def get_doc(self) -> Optional[List[List[str]]]:
        """Get the docstring of the object."""
        docstring = super().get_doc()
        if docstring:
            # Process doc comments in function docstrings
            processed_docstring = self._process_doc_comments(docstring)
            return processed_docstring
        return docstring

    def _process_doc_comments(self, docstring: List[List[str]]) -> List[List[str]]:
        """Process doc comments in the docstring."""
        processed = []
        for section in docstring:
            processed_section = []
            for line in section:
                stripped = line.strip()
                if stripped.startswith("#"):
                    # Convert doc comment to regular docstring line
                    comment_content = stripped[1:].strip()
                    if comment_content:
                        processed_section.append(comment_content)
                else:
                    processed_section.append(line)
            processed.append(processed_section)
        return processed

    def add_content(self, more_content: Optional[List[nodes.Node]]) -> None:
        """Add content from docstrings, autodoc and user."""
        # Enhanced content processing for all functions
        if hasattr(self, "doc_as_astree") and self.doc_as_astree:
            self._process_enhanced_function_patterns()

        super().add_content(more_content)

    def _process_enhanced_function_patterns(self) -> None:
        """Process enhanced function patterns for all modules."""
        if not self.docstring:
            return

        docstring = str(self.docstring)

        # Enhance function descriptions for all modules
        patterns = [
            # Function definitions
            (r"def (\w+)\s*\(", r"Function: \1"),
            (r"@(\w+)", r"Decorator: \1"),
            # Common library references
            (r"gradio\.(\w+)", r"Gradio \1 component"),
            (r"openai\.(\w+)", r"OpenAI \1"),
            (r"torch\.(\w+)", r"PyTorch \1"),
            (r"tensorflow\.(\w+)", r"TensorFlow \1"),
            (r"sklearn\.(\w+)", r"Scikit-learn \1"),
            (r"numpy\.(\w+)", r"NumPy \1"),
            (r"pandas\.(\w+)", r"Pandas \1"),
            # Google-style docstring sections
            (r"Args?:", "**Arguments:**"),
            (r"Returns?:", "**Returns:**"),
            (r"Raises?:", "**Raises:**"),
            (r"Yields?:", "**Yields:**"),
            (r"Example:", "**Example:**"),
            (r"Examples:", "**Examples:**"),
            (r"Note:", "**Note:**"),
            (r"Warning:", "**Warning:**"),
            # Parameter descriptions
            (r"(\w+):\s*(\w+)", r"\1: \2"),
            (r"returns?:\s*(\w+)", r"Returns: \1"),
            (r"args?:\s*(\w+)", r"Arguments: \1"),
        ]

        for pattern, replacement in patterns:
            docstring = re.sub(pattern, replacement, docstring)

        if docstring != str(self.docstring):
            self.docstring = docstring


class EnhancedClassDocumenter(ClassDocumenter):
    """Enhanced class documenter with better docstring parsing."""

    def get_doc(self) -> Optional[List[List[str]]]:
        """Get the docstring of the object."""
        docstring = super().get_doc()
        if docstring:
            # Process doc comments in class docstrings
            processed_docstring = self._process_doc_comments(docstring)
            return processed_docstring
        return docstring

    def _process_doc_comments(self, docstring: List[List[str]]) -> List[List[str]]:
        """Process doc comments in the docstring."""
        processed = []
        for section in docstring:
            processed_section = []
            for line in section:
                stripped = line.strip()
                if stripped.startswith("#"):
                    # Convert doc comment to regular docstring line
                    comment_content = stripped[1:].strip()
                    if comment_content:
                        processed_section.append(comment_content)
                else:
                    processed_section.append(line)
            processed.append(processed_section)
        return processed

    def add_content(self, more_content: Optional[List[nodes.Node]]) -> None:
        """Add content from docstrings, autodoc and user."""
        # Enhanced content processing for all classes
        if hasattr(self, "doc_as_astree") and self.doc_as_astree:
            self._process_enhanced_class_patterns()

        super().add_content(more_content)

    def _process_enhanced_class_patterns(self) -> None:
        """Process enhanced class patterns for all modules."""
        if not self.docstring:
            return

        docstring = str(self.docstring)

        # Enhance class descriptions for all modules
        patterns = [
            # Class definitions
            (r"class (\w+)", r"Class: \1"),
            (r"def (\w+)\s*\(", r"Method: \1"),
            (r"@(\w+)", r"Decorator: \1"),
            # Common library references
            (r"gradio\.(\w+)", r"Gradio \1 component"),
            (r"openai\.(\w+)", r"OpenAI \1"),
            (r"torch\.(\w+)", r"PyTorch \1"),
            (r"tensorflow\.(\w+)", r"TensorFlow \1"),
            (r"sklearn\.(\w+)", r"Scikit-learn \1"),
            (r"numpy\.(\w+)", r"NumPy \1"),
            (r"pandas\.(\w+)", r"Pandas \1"),
            # Google-style docstring sections
            (r"Args?:", "**Arguments:**"),
            (r"Returns?:", "**Returns:**"),
            (r"Raises?:", "**Raises:**"),
            (r"Yields?:", "**Yields:**"),
            (r"Example:", "**Example:**"),
            (r"Examples:", "**Examples:**"),
            (r"Note:", "**Note:**"),
            (r"Warning:", "**Warning:**"),
            # Class-specific patterns
            (r"__init__", "Constructor"),
            (r"__str__", "String representation"),
            (r"__repr__", "Representation"),
        ]

        for pattern, replacement in patterns:
            docstring = re.sub(pattern, replacement, docstring)

        if docstring != str(self.docstring):
            self.docstring = docstring


def setup(app: Sphinx) -> Dict[str, Any]:
    """Set up the enhanced docstring parsing extension."""

    # Register enhanced documenters
    app.add_autodocumenter(EnhancedModuleDocumenter, override=True)
    app.add_autodocumenter(EnhancedFunctionDocumenter, override=True)
    app.add_autodocumenter(EnhancedClassDocumenter, override=True)

    # Configure Napoleon to use enhanced docstring parsers
    app.config.napoleon_google_docstring = True
    app.config.napoleon_numpy_docstring = True

    # Add custom docstring processors
    app.add_config_value("docstring_style", "google,sphinx", "env")
    app.add_config_value("docstring_options", {}, "env")

    # Add enhanced docstring configuration
    app.add_config_value("enhance_docstrings", True, "env")
    app.add_config_value("google_style_enhancement", True, "env")

    # Connect to events for better docstring processing
    app.connect("autodoc-process-docstring", process_enhanced_docstring)

    return {
        "version": "1.0.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def process_enhanced_docstring(
    app: Sphinx,
    what: str,
    name: str,
    obj: Any,
    options: Dict[str, Any],
    lines: List[str],
) -> None:
    """Process docstrings to enhance all module documentation with Google-style formatting."""
    if not app.config.enhance_docstrings:
        return

    # Process all modules, not just specific ones
    enhanced_lines = []

    for line in lines:
        # Enhance common patterns across all modules
        enhanced_line = line

        # Enhance function definitions
        enhanced_line = re.sub(r"def (\w+)\s*\(", r"Function: \1", enhanced_line)

        # Enhance class definitions
        enhanced_line = re.sub(r"class (\w+)", r"Class: \1", enhanced_line)

        # Enhance decorators
        enhanced_line = re.sub(r"@(\w+)", r"Decorator: \1", enhanced_line)

        # Enhance common library references
        enhanced_line = re.sub(r"gradio\.(\w+)", r"Gradio \1 component", enhanced_line)
        enhanced_line = re.sub(r"openai\.(\w+)", r"OpenAI \1", enhanced_line)
        enhanced_line = re.sub(r"torch\.(\w+)", r"PyTorch \1", enhanced_line)
        enhanced_line = re.sub(r"tensorflow\.(\w+)", r"TensorFlow \1", enhanced_line)
        enhanced_line = re.sub(r"sklearn\.(\w+)", r"Scikit-learn \1", enhanced_line)

        # Enhance Google-style docstring sections
        enhanced_line = re.sub(r"Args?:", "**Arguments:**", enhanced_line)
        enhanced_line = re.sub(r"Returns?:", "**Returns:**", enhanced_line)
        enhanced_line = re.sub(r"Raises?:", "**Raises:**", enhanced_line)
        enhanced_line = re.sub(r"Yields?:", "**Yields:**", enhanced_line)
        enhanced_line = re.sub(r"Example:", "**Example:**", enhanced_line)
        enhanced_line = re.sub(r"Examples:", "**Examples:**", enhanced_line)
        enhanced_line = re.sub(r"Note:", "**Note:**", enhanced_line)
        enhanced_line = re.sub(r"Warning:", "**Warning:**", enhanced_line)

        # Enhance type hints
        enhanced_line = re.sub(r"(\w+):\s*(\w+)", r"\1: \2", enhanced_line)

        # Enhance parameter descriptions
        enhanced_line = re.sub(
            r"(\w+)\s*\(([^)]+)\):\s*(.+)", r"\1 (\2): \3", enhanced_line
        )

        enhanced_lines.append(enhanced_line)

    # Replace the lines with enhanced versions
    lines[:] = enhanced_lines
