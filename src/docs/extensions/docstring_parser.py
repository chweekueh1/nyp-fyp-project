#!/usr/bin/env python3
"""
Custom Sphinx extension for enhanced docstring parsing.

This extension provides improved support for both Google and Sphinx style docstrings,
and ensures that doc comments are properly processed.
"""

import re
import ast
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
    """Enhanced module documenter with better docstring parsing and context labeling."""

    def get_doc(self) -> Optional[List[List[str]]]:
        """Get the docstring of the object, with context and fallback extraction for scripts/tests/roots. Also writes a .rst file for the module."""
        try:
            docstring = super().get_doc()
        except Exception as e:
            module_path = (
                getattr(self, "modname", None) or getattr(self, "fullname", None) or ""
            )
            warning_msg = f".. warning:: Module '{module_path}' could not be imported or parsed: {str(e)}"
            return [[warning_msg]]

        module_path = (
            getattr(self, "modname", None) or getattr(self, "fullname", None) or ""
        )
        context_label = self._get_context_label(module_path)
        if not docstring or not any(
            any(line.strip() for line in section) for section in docstring
        ):
            summary = self._extract_summary_from_source()
            if summary:
                docstring = [[summary]]
            else:
                docstring = [
                    [
                        f".. warning:: No module-level docstring found for {module_path or 'unknown module'}"
                    ]
                ]
        if context_label:
            docstring = [[f"**{context_label}**"]] + docstring
        processed_docstring = self._process_doc_comments(docstring)

        # --- RST file generation ---
        try:
            import os
            import inspect

            # Always write to src/docs/modules
            output_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../modules")
            )
            os.makedirs(output_dir, exist_ok=True)
            module_name = module_path.split(".")[-1] if module_path else "module"
            rst_path = os.path.join(output_dir, f"{module_name}.rst")
            title = f"{module_name} module"
            rst_lines = [
                title,
                "=" * len(title),
                "",
                ".. module:: " + module_path,
                "",
                "Docstring:",
                "----------",
                "",
            ]
            # Always include the enhanced docstring, even if empty
            for section in processed_docstring:
                for line in section:
                    rst_lines.append(line)
                rst_lines.append("")
            # Add function/class listing if possible
            if hasattr(self, "object") and inspect.ismodule(self.object):
                members = inspect.getmembers(self.object)
                functions = [name for name, obj in members if inspect.isfunction(obj)]
                classes = [name for name, obj in members if inspect.isclass(obj)]
                if functions:
                    rst_lines.append("Functions:")
                    rst_lines.append("~~~~~~~~~~")
                    for func in functions:
                        rst_lines.append(f"- ``{func}``")
                    rst_lines.append("")
                if classes:
                    rst_lines.append("Classes:")
                    rst_lines.append("~~~~~~~~")
                    for cls in classes:
                        rst_lines.append(f"- ``{cls}``")
                    rst_lines.append("")
            with open(rst_path, "w", encoding="utf-8") as rst_file:
                rst_file.write("\n".join(rst_lines))
            print(f"[docstring_parser] Wrote RST for {module_path} to {rst_path}")
        except Exception as e:
            import sys

            print(
                f"[docstring_parser] Failed to write RST for {module_path}: {e}",
                file=sys.stderr,
            )
        # --- End RST file generation ---

        return processed_docstring

    def _get_context_label(self, module_path: str) -> str:
        if module_path.startswith("scripts.") or module_path == "scripts":
            return "[Script]"
        if module_path.startswith("tests.") or module_path == "tests":
            return "[Test]"
        if "." not in module_path and module_path:
            return "[Root Module]"
        if module_path.endswith(".__init__"):
            return "[Package]"
        return ""

    def _extract_summary_from_source(self) -> Optional[str]:
        # Try to extract a summary from the first function/class or top-level comments
        try:
            if not hasattr(self, "object") or not hasattr(self.object, "__file__"):
                return None
            source_path = self.object.__file__
            with open(source_path, "r", encoding="utf-8") as f:
                source = f.read()

            # Skip shebang line if present
            lines = source.splitlines()
            start_line = 0
            if lines and lines[0].startswith("#!"):
                start_line = 1
                source = "\n".join(lines[1:])

            # Try to parse the source
            try:
                tree = ast.parse(source)
                # --- AST file generation ---
                import os

                ast_dump = ast.dump(tree, indent=2)
                ast_path = os.path.splitext(source_path)[0] + ".ast"
                with open(ast_path, "w", encoding="utf-8") as ast_file:
                    ast_file.write(ast_dump)
            except SyntaxError as e:
                # If parsing fails, try with the original source (including shebang)
                try:
                    tree = ast.parse("\n".join(lines))
                    start_line = 0
                    # --- AST file generation ---
                    import os

                    ast_dump = ast.dump(tree, indent=2)
                    ast_path = os.path.splitext(source_path)[0] + ".ast"
                    with open(ast_path, "w", encoding="utf-8") as ast_file:
                        ast_file.write(ast_dump)
                except SyntaxError:
                    # If still failing, return a warning about syntax errors
                    module_path = getattr(self, "modname", "unknown")
                    print(f"Warning: Syntax error in {module_path}: {e}")
                    return f".. warning:: Module has syntax errors: {str(e)}"

            # Try module docstring first
            mod_doc = ast.get_docstring(tree)
            if mod_doc:
                return mod_doc.strip()

            # If no module docstring, look for docstrings in the first few nodes
            # This handles cases where docstrings come after imports
            for node in tree.body[:5]:  # Check first 5 nodes
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                    # This is a string literal at module level (likely a docstring)
                    doc = node.value.s.strip()
                    if doc and len(doc) > 20:  # Reasonable length for a docstring
                        return doc
                elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    doc = ast.get_docstring(node)
                    if doc:
                        return doc.strip()

            # Try top-level comments (but skip shebang and encoding lines)
            comments = []
            for i, line in enumerate(lines[start_line:], start_line):
                stripped = line.strip()
                if stripped.startswith("#") and not stripped.startswith("#!"):
                    comment_content = stripped[1:].strip()
                    if comment_content and len(comment_content) > 10:
                        comments.append(comment_content)
                        if len(comments) >= 3:  # Limit to first 3 meaningful comments
                            break

            if comments:
                return " ".join(comments[:2])  # Return first 2 comments as summary

            # Generate a basic description based on the module name and content
            module_name = getattr(self, "modname", "unknown")
            if module_name:
                # Special handling for __init__.py files
                if module_name.endswith(".__init__"):
                    package_name = module_name.replace(".__init__", "")
                    return f"Package initialization module for {package_name.replace('_', ' ')}. Contains package-level imports, exports, and configuration."

                # Analyze the module content to generate a basic description
                has_functions = any(
                    isinstance(node, ast.FunctionDef) for node in tree.body
                )
                has_classes = any(isinstance(node, ast.ClassDef) for node in tree.body)
                has_imports = any(
                    isinstance(node, (ast.Import, ast.ImportFrom)) for node in tree.body
                )

                description_parts = []
                if has_functions:
                    description_parts.append("functions")
                if has_classes:
                    description_parts.append("classes")
                if has_imports:
                    description_parts.append("imports")

                if description_parts:
                    return f"Module containing {', '.join(description_parts)} for {module_name.replace('_', ' ')} functionality."

        except Exception as e:
            # Log the error but don't fail completely
            module_path = getattr(self, "modname", "unknown")
            print(f"Warning: Could not extract summary from {module_path}: {e}")
            return f".. warning:: Could not extract summary: {str(e)}"
        return None

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
            # Sphinx-style docstring fields (preserve as-is)
            (
                r"(:param[\s\w,]*:|:type[\s\w,]*:|:return:|:rtype:|:raises[\s\w,]*:|:var[\s\w,]*:|:ivar[\s\w,]*:|:cvar[\s\w,]*:)",
                r"\\1",
            ),
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

    # Only register EnhancedGoogleDocstring for napoleon config
    app.config.napoleon_google_docstring = True
    app.config.napoleon_numpy_docstring = True
    app.add_config_value("enhanced_google_docstring", "EnhancedGoogleDocstring", "env")
    # Do NOT register EnhancedNumpyDocstring

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

    # Safeguard: Only process if not already enhanced (add a marker comment)
    if lines and any("[ENHANCED_DOCSTRING]" in line for line in lines):
        return

    enhanced_lines = []
    for line in lines:
        enhanced_line = line
        # Only match section headers at the start of lines
        enhanced_line = re.sub(r"^Args?:", "**Arguments:**", enhanced_line)
        enhanced_line = re.sub(r"^Returns?:", "**Returns:**", enhanced_line)
        enhanced_line = re.sub(r"^Raises?:", "**Raises:**", enhanced_line)
        enhanced_line = re.sub(r"^Yields?:", "**Yields:**", enhanced_line)
        enhanced_line = re.sub(r"^Example:", "**Example:**", enhanced_line)
        enhanced_line = re.sub(r"^Examples:", "**Examples:**", enhanced_line)
        enhanced_line = re.sub(r"^Note:", "**Note:**", enhanced_line)
        enhanced_line = re.sub(r"^Warning:", "**Warning:**", enhanced_line)
        # Enhance function/class/other patterns (keep as before)
        enhanced_line = re.sub(r"def (\w+)\s*\(", r"Function: \1", enhanced_line)
        enhanced_line = re.sub(r"class (\w+)", r"Class: \1", enhanced_line)
        enhanced_line = re.sub(r"@(\w+)", r"Decorator: \1", enhanced_line)
        enhanced_line = re.sub(r"gradio\.(\w+)", r"Gradio \1 component", enhanced_line)
        enhanced_line = re.sub(r"openai\.(\w+)", r"OpenAI \1", enhanced_line)
        enhanced_line = re.sub(r"torch\.(\w+)", r"PyTorch \1", enhanced_line)
        enhanced_line = re.sub(r"tensorflow\.(\w+)", r"TensorFlow \1", enhanced_line)
        enhanced_line = re.sub(r"sklearn\.(\w+)", r"Scikit-learn \1", enhanced_line)
        # Enhance type hints and parameter descriptions (optional, can be commented out if too aggressive)
        # enhanced_line = re.sub(r"(\w+):\s*(\w+)", r"\1: \2", enhanced_line)
        # enhanced_line = re.sub(r"(\w+)\s*\(([^)]+)\):\s*(.+)", r"\1 (\2): \3", enhanced_line)
        enhanced_lines.append(enhanced_line)
    # Add a marker to prevent double-processing
    enhanced_lines.append("[ENHANCED_DOCSTRING]")
    lines[:] = enhanced_lines
