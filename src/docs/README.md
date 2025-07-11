# Documentation Directory

This directory contains the Sphinx documentation for the NYP FYP CNC Chatbot project.

## Structure

- `conf.py` - Sphinx configuration file
- `index.rst` - Main documentation index
- `Makefile` - Build commands for documentation
- `examples/` - Example files demonstrating docstring styles
  - `docstring_styles.py` - Examples of Google, Sphinx, and NumPy style docstrings

## Building Documentation

To build the documentation:

```bash
# From the project root
python src/scripts/generate_docs.py

# Or from the docs directory
make html
```

**Note:** RST files are now auto-generated and managed inside the Docker container. Do not edit or generate them locally. Use the Docker workflow for documentation builds.

## Features

- **Multi-style docstring support**: Google, Sphinx, and NumPy styles using built-in Sphinx extensions
- **Standard autodoc**: Uses sphinx-apidoc for automatic module discovery
- **Built-in parsing**: Leverages Napoleon extension for Google/NumPy styles and standard autodoc for Sphinx styles
- **Missing docstring detection**: Automatically adds helpful messages for files without proper docstrings

## Configuration

The documentation is configured in `conf.py` with the following key features:

- Napoleon extension for Google/NumPy style docstrings
- Standard autodoc for Sphinx style docstrings
- Light theme by default
- Comprehensive autodoc settings
- Mock imports for external dependencies
- Automatic missing docstring detection

## Built-in Extensions

The documentation system uses standard Sphinx extensions:

- **sphinx.ext.napoleon**: Handles Google and NumPy style docstrings
- **sphinx.ext.autodoc**: Handles Sphinx style docstrings and automatic module discovery
- **sphinx-apidoc**: Generates RST files from Python modules

## Examples

See `examples/docstring_styles.py` for examples of:

- Google-style docstrings
- Sphinx-style docstrings
- NumPy-style docstrings (not enhanced by the custom extension)
- Doc comments in docstrings
- Class and method documentation
- Property documentation
