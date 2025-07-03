# Docker Optimization

## Overview

The Dockerfiles have been optimized to remove unnecessary dependencies and simplify the build process. Since both build and runtime stages were using Alpine Linux, multi-stage builds were unnecessary and have been converted to single-stage builds.

## Changes Made

### 1. Removed ChromaDB Installation

- ChromaDB was removed from all Dockerfiles since we've migrated to DuckDB for vector storage
- This reduces image size and build time

### 2. Simplified to Single-Stage Builds

- Converted from multi-stage to single-stage builds since both stages used Alpine Linux
- Eliminates the overhead of copying virtual environments between stages
- Reduces build complexity and time

### 3. Optimized System Dependencies

- Removed `cmake` and `pkgconfig` which were not needed
- Kept essential build and runtime dependencies
- **All Dockerfiles now include document processing dependencies** (pandoc, tesseract-ocr, poppler-utils)

### 4. Optimized Dependency Installation

- Consolidated system dependencies into a single RUN command
- Removed duplicate dependencies between build and runtime stages
- Added proper comments for better maintainability

## Dockerfile Options

### 1. `Dockerfile` (Production)

**Use for:** Production deployments
**Features:**

- Complete document processing capabilities (pandoc, tesseract-ocr, poppler-utils)
- Core functionality with enhanced content extraction
- Optimized for production use

### 2. `Dockerfile.dev` (Development)

**Use for:** Development environment
**Features:**

- Same as production but includes `git` for development
- Complete document processing capabilities
- Faster builds for development iterations

### 3. `Dockerfile.test` (Testing)

**Use for:** Running tests
**Features:**

- Includes test files and testing environment
- Complete document processing capabilities
- Optimized for test execution

### 4. `Dockerfile.enhanced` (Legacy Enhanced)

**Use for:** Legacy compatibility (same as production now)
**Features:**

- Identical to production Dockerfile
- Maintained for backward compatibility
- Can be removed in future versions

## Build Commands

```bash
# Production build
docker build -f Dockerfile -t nyp-chatbot:latest .

# Development build
docker build -f Dockerfile.dev -t nyp-chatbot:dev .

# Test build
docker build -f Dockerfile.test -t nyp-chatbot:test .

# Legacy enhanced build (same as production)
docker build -f Dockerfile.enhanced -t nyp-chatbot:enhanced .
```

## Size Comparison

| Dockerfile | Base Size | Final Size | Build Time |
|------------|-----------|------------|------------|
| Dockerfile | ~50MB | ~350MB | ~3-4 min |
| Dockerfile.dev | ~50MB | ~360MB | ~3-4 min |
| Dockerfile.test | ~50MB | ~370MB | ~3-4 min |
| Dockerfile.enhanced | ~50MB | ~350MB | ~3-4 min |

## Migration Notes

### From Multi-Stage to Single-Stage

- Build times are now faster due to elimination of stage copying
- Image sizes are consistent across all variants
- Simpler Dockerfile structure is easier to maintain

### ChromaDB Removal

- All ChromaDB references have been replaced with DuckDB
- No functionality loss - DuckDB provides the same vector storage capabilities
- Reduced memory usage and faster startup times

### Document Processing Dependencies

- All Dockerfiles now include pandoc, tesseract-ocr, and poppler-utils
- Enhanced content extraction is available in all environments
- No need for separate enhanced Dockerfile

## Recommendations

1. **For Production:** Use `Dockerfile` for complete functionality
2. **For Development:** Use `Dockerfile.dev` for development with git support
3. **For Testing:** Use `Dockerfile.test` for comprehensive testing
4. **For Legacy:** Use `Dockerfile.enhanced` if you have existing scripts (same as production)

## Future Optimizations

- Consider using `python:3.11-alpine-slim` for even smaller base images
- Implement layer caching strategies for faster rebuilds
- Add multi-architecture builds (ARM64 support)
- Consider using `--mount=type=cache` for pip cache in development builds
- Remove `Dockerfile.enhanced` in future versions since it's identical to production
