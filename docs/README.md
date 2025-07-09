# Documentation Directory

This directory contains the Sphinx documentation for the NYP FYP CNC Chatbot project.

## Structure

- `conf.py` - Sphinx configuration file
- `index.rst` - Main documentation index
- `Makefile` - Build commands for documentation
- `extensions/` - Custom Sphinx extensions
  - `docstring_parser.py` - Enhanced docstring parsing for Google and Sphinx styles
- `examples/` - Example files demonstrating docstring styles
  - `docstring_styles.py` - Examples of Google, Sphinx, and NumPy style docstrings

## Building Documentation

To build the documentation:

```bash
# From the project root
python scripts/generate_docs.py

# Or from the docs directory
make html
```

**Note:** RST files are now auto-generated and managed inside the Docker container. Do not edit or generate them locally. Use the Docker workflow for documentation builds.

## Features

- **Multi-style docstring support**: Google, Sphinx, and NumPy styles
- **Doc comment processing**: Handles `#` comments in docstrings
- **Enhanced autodoc**: Better parameter and return type documentation
- **Custom extensions**: Improved parsing and formatting

## Configuration

The documentation is configured in `conf.py` with the following key features:

- Napoleon extension for Google/NumPy style docstrings
- Custom docstring parser extension
- Light theme by default
- Comprehensive autodoc settings
- Mock imports for external dependencies

## Extensions

### docstring_parser.py

This custom extension provides:

- Enhanced Google-style docstring parsing
- Enhanced NumPy-style docstring parsing
- Doc comment processing (converts `#` comments to docstring content)
- Better handling of both docstring styles in the same codebase

## Examples

See `examples/docstring_styles.py` for examples of:

- Google-style docstrings
- Sphinx-style docstrings
- NumPy-style docstrings
- Doc comments in docstrings
- Class and method documentation
- Property documentation
