# Documentation Generation System

This document describes the comprehensive Sphinx documentation generation system for the NYP FYP CNC Chatbot project.

## Overview

The project includes an automated documentation generation system that creates comprehensive API documentation for all Python modules, functions, and classes. The documentation is built using Sphinx and served via HTTP in a Docker container.

## Quick Start

```bash
# Generate and serve documentation
python setup.py --docs
```

The documentation will be available at <http://localhost:8080>

## Architecture

### Components

1. **Dockerfile.docs**: Specialized Docker image for documentation building
2. **scripts/generate_docs.py**: Main documentation generation script
3. **scripts/serve_docs.sh**: HTTP server for serving documentation
4. **docs/conf.py**: Sphinx configuration
5. **docs/index.rst**: Documentation index and structure
6. **requirements-docs.txt**: Documentation-specific dependencies

### Build Process

1. **Docker Build**: Creates container with all documentation dependencies
2. **Module Discovery**: Recursively finds all Python files in the project
3. **API Documentation**: Generates RST files for each module using sphinx-apidoc
4. **Package Organization**: Creates package index files for better navigation
5. **HTML Generation**: Builds final HTML documentation using Sphinx
6. **HTTP Server**: Serves documentation on port 8080

## What Gets Documented

### Backend Modules (`backend/`)

- `auth.py`: Authentication and user management
- `chat.py`: Chat functionality and message handling
- `database.py`: Database operations and data persistence
- `file_handling.py`: File upload and processing
- `audio.py`: Audio processing and transcription
- `config.py`: Configuration management
- `rate_limiting.py`: Rate limiting utilities
- `utils.py`: Backend utilities
- `markdown_formatter.py`: Markdown formatting utilities
- `timezone_utils.py`: Timezone handling utilities

### Gradio Interface (`gradio_modules/`)

- `chatbot.py`: Core chatbot component
- `file_upload.py`: File upload interface
- `file_classification.py`: File classification UI
- `audio_input.py`: Audio input component
- `search_interface.py`: Search functionality
- `login_and_register.py`: Authentication UI
- `change_password.py`: Password change interface
- `enhanced_content_extraction.py`: Content extraction
- `classification_formatter.py`: Classification formatting

### LLM Components (`llm/`)

- `chatModel.py`: Chat model implementation
- `classificationModel.py`: Classification model
- `dataProcessing.py`: Data processing utilities
- `keyword_cache.py`: Keyword caching system

### Infrastructure (`infra_utils/`, `scripts/`)

- `infra_utils.py`: Infrastructure utilities
- `infra_utils/nltk_config.py`: NLTK configuration
- All utility scripts in `scripts/`

### Test Suite (`tests/`)

- All test files in `tests/backend/`
- All test files in `tests/frontend/`
- All test files in `tests/integration/`
- All test files in `tests/performance/`
- All test files in `tests/llm/`
- All test files in `tests/utils/`
- All demo files in `tests/demos/`

### Root Modules

- `app.py`: Main application entry point
- `setup.py`: Build and deployment automation
- `system_prompts.py`: System prompt definitions
- `performance_utils.py`: Performance optimization utilities
- `hashing.py`: Password hashing utilities
- `flexcyon_theme.py`: Custom Gradio theme

## Documentation Features

### Complete API Coverage

- All Python modules are automatically discovered and documented
- Function signatures with type hints
- Class documentation with inheritance information
- Module-level documentation and imports

### Cross-Reference Support

- Links between related functions and modules
- Automatic linking of imported types
- Navigation between different sections

### Search Functionality

- Full-text search across all documentation
- Module and function name search
- Search result highlighting

### Modern Theme

- Uses Piccolo theme for clean, responsive design
- Mobile-friendly layout
- Dark/light mode support
- Syntax highlighting for code examples

## Troubleshooting

### UV Installation Failures

The documentation build uses `uv` for fast dependency installation. Occasionally, `uv` may fail due to network connectivity issues:

```
error: Failed to fetch: `https://pypi.org/simple/pypdfium2/`
Caused by: peer closed connection without sending TLS close_notify
```

**Solution**: Simply try again - this is usually a temporary network issue:

```bash
# Clean up and retry
python setup.py --docker-wipe
python setup.py --docs
```

**Why this happens**: `uv` uses Rust-based networking which can be sensitive to TLS handshake issues in some Docker environments. The failure is temporary and retrying usually resolves it.

### Common Issues and Solutions

#### 1. Port 8080 Already in Use

```bash
# Check what's using the port
lsof -i :8080

# Kill the process or use a different port
kill -9 <PID>
```

#### 2. Docker Build Fails

```bash
# Clean up Docker and retry
python setup.py --docker-wipe
python setup.py --docs
```

#### 3. Documentation Not Updating

```bash
# Force rebuild by wiping Docker cache
python setup.py --docker-wipe
python setup.py --docs
```

#### 4. Missing Modules in Documentation

- Ensure all Python files have proper docstrings
- Check that files are not excluded by `.dockerignore`
- Verify that the module is in a directory being processed

#### 5. Sphinx Build Warnings

- Most warnings are informational and don't affect functionality
- Check `docs/conf.py` for warning suppression settings
- Some warnings about missing titles are expected for test files

## Advanced Usage

### Manual Docker Commands

If you prefer to build documentation manually:

```bash
# Build documentation container
docker build --progress=plain -f Dockerfile.docs -t nyp-fyp-chatbot:docs .

# Run documentation server
docker run --name nyp-fyp-chatbot-docs -p 8080:8080 nyp-fyp-chatbot:docs
```

### Local Documentation Development

For documentation development without Docker:

```bash
# Install documentation dependencies
pip install -r requirements-docs.txt

# Generate documentation locally
cd docs
sphinx-apidoc -o modules --separate --module-first --maxdepth=6 --private --no-headings ../backend ../gradio_modules ../llm ../infra_utils ../scripts ../tests ../misc ../
sphinx-build -b html . _build/html

# Serve locally
python -m http.server 8080 --directory _build/html
```

### Customizing Documentation

#### Adding New Modules

New Python modules are automatically discovered and documented. Just ensure they have proper docstrings.

#### Modifying Theme

Edit `docs/conf.py` to change the Sphinx theme or configuration options.

#### Adding Custom Pages

Create `.rst` files in the `docs/` directory and add them to the toctree in `docs/index.rst`.

#### Updating Structure

Modify `scripts/generate_docs.py` to change how modules are organized in the documentation.

## Configuration Files

### docs/conf.py

- Sphinx configuration and extensions
- Theme settings (Piccolo theme)
- Autodoc settings for API documentation
- Intersphinx mappings for external references

### scripts/generate_docs.py

- Module discovery and processing
- Package index file generation
- Sphinx-apidoc command execution
- Documentation structure organization

### scripts/serve_docs.sh

- HTTP server startup
- Graceful shutdown handling
- Port configuration
- Build process orchestration

### requirements-docs.txt

- Sphinx and documentation dependencies
- Theme packages (piccolo-theme)
- Additional documentation tools

## Performance Considerations

### Build Time

- Initial build: ~2-3 minutes (includes Docker image creation)
- Subsequent builds: ~30-60 seconds (uses Docker cache)
- Documentation generation: ~10-30 seconds

### Resource Usage

- Docker container: ~500MB disk space
- Memory usage: ~200MB during build
- Network: Downloads dependencies on first build

### Optimization Tips

- Use Docker cache for faster rebuilds
- Exclude unnecessary files in `.dockerignore`
- Consider using `--no-cache` only when needed

## Integration with Development Workflow

### Pre-commit Integration

Documentation generation can be integrated with pre-commit hooks to ensure documentation stays up-to-date.

### CI/CD Integration

The documentation build can be automated in CI/CD pipelines to generate documentation for each release.

### Version Control

- Documentation source files are version controlled
- Generated HTML is not version controlled (built in Docker)
- Documentation reflects the current state of the codebase

## Future Enhancements

### Planned Features

- PDF documentation generation
- API documentation for external integrations
- Interactive code examples
- User guide and tutorials
- Performance benchmarks documentation

### Potential Improvements

- Faster build times with incremental builds
- Better search functionality
- More customization options
- Integration with external documentation services
