# Dependency Fixes Summary

This document outlines the fixes made to resolve missing dependencies in the NYP FYP Chatbot project.

## Issues Identified

### 1. Missing Python Package: `langchain-community`

**Problem**: The `llm/dataProcessing.py` file imports from `langchain_community` but this package was not listed in `requirements.txt`.

**Files Affected**:

- `llm/dataProcessing.py` (lines 1-2)
- `requirements.txt`

**Fix**: Added `langchain-community==0.3.23` to `requirements.txt`

### 2. Missing System Dependencies in Dockerfiles

**Problem**: The Dockerfiles were missing essential system tools for document processing:

- `pandoc` - Document conversion (.docx, .doc, .odt, .rtf, .html, .epub, .md)
- `tesseract-ocr` - OCR for image text extraction
- `poppler-utils` - PDF processing utilities

**Files Affected**:

- `Dockerfile`
- `Dockerfile.dev`
- `Dockerfile.test`

**Fix**: Added the following packages to all Dockerfiles:

```dockerfile
# Document processing dependencies
pandoc \
tesseract-ocr \
tesseract-ocr-eng \
poppler-utils \
# Additional dependencies for better OCR and document processing
libtesseract-dev \
libpoppler-cpp-dev \
```

## Changes Made

### 1. Updated `requirements.txt`

```diff
langchain==0.3.23
langchain-chroma==0.2.2
+ langchain-community==0.3.23
langchain-core==0.3.51
langchain-openai==0.3.12
```

### 2. Updated All Dockerfiles

Added system dependencies for document processing:

- **pandoc**: Universal document converter
- **tesseract-ocr**: OCR engine for text extraction from images
- **tesseract-ocr-eng**: English language pack for Tesseract
- **poppler-utils**: PDF processing utilities (includes pdftotext)
- **libtesseract-dev**: Development libraries for Tesseract
- **libpoppler-cpp-dev**: Development libraries for Poppler

### 3. Created Dependency Test Script

Created `tests/test_dependencies.py` to verify all dependencies are properly installed:

- Tests Python package imports
- Tests system tool availability
- Tests system tool functionality
- Tests specific LangChain imports used in the codebase

### 4. Integrated into Test Suites

Added dependency tests to the existing test infrastructure:

**Main Test Runner** (`tests/run_all_tests.py`):

- Added `run_dependency_tests()` function
- Added "Dependency Tests" as the first test suite to run
- Added `--suite dependencies` command line option
- Dependency tests now run before all other tests

**Comprehensive Test Suite** (`tests/comprehensive_test_suite.py`):

- Added `run_dependency_tests()` method to TestSuite class
- Added dependency tests as the first category in comprehensive suite
- Added `--suite dependencies` option for standalone dependency testing

## Verification

To verify the fixes work correctly:

### 1. Test Python Dependencies

```bash
# Run dependency tests only
python tests/test_dependencies.py

# Run through main test runner
python tests/run_all_tests.py --suite dependencies

# Run through comprehensive test suite
python tests/comprehensive_test_suite.py --suite dependencies
```

### 2. Test Docker Build

```bash
# Test production build
docker build --progress=plain -t nyp-fyp-chatbot .

# Test development build
docker build --progress=plain -f Dockerfile.dev -t nyp-fyp-chatbot-dev .

# Test with dependency verification
docker build --progress=plain -f Dockerfile.test -t nyp-fyp-chatbot-test .
docker run nyp-fyp-chatbot-test
```

### 3. Test System Tools

The dependency test script will verify:

- ✅ `pandoc --version` works
- ✅ `tesseract --version` works
- ✅ `pdftotext -v` works (poppler-utils)

### 4. Test Integration

```bash
# Run all tests (dependencies will be tested first)
python tests/run_all_tests.py

# Run comprehensive test suite (dependencies included)
python tests/comprehensive_test_suite.py
```

## Impact

These fixes ensure:

1. **Complete LangChain Functionality**: All LangChain imports work correctly
2. **Document Processing**: Full support for various document formats via Pandoc
3. **OCR Capabilities**: Text extraction from images via Tesseract
4. **PDF Processing**: Enhanced PDF handling via Poppler utilities
5. **Docker Compatibility**: All dependencies are properly installed in containerized environments
6. **Test Integration**: Dependency verification is now part of the standard test workflow

## Test Integration Details

### Main Test Runner Integration

- **Position**: Dependency tests run first (before backend, frontend, integration, LLM tests)
- **Command**: `python tests/run_all_tests.py --suite dependencies`
- **Output**: Clear pass/fail status with detailed error messages

### Comprehensive Test Suite Integration

- **Position**: Dependency tests are the first category in the comprehensive suite
- **Command**: `python tests/comprehensive_test_suite.py --suite dependencies`
- **Output**: Integrated with overall test summary and success rate calculation

### Docker Test Integration

- **Dockerfile.test**: Now runs dependency tests by default
- **Command**: `docker run nyp-fyp-chatbot-test`
- **Output**: Comprehensive dependency verification in containerized environment

## Notes

- The Docker images will be slightly larger due to the additional system dependencies
- All dependencies are essential for the enhanced file classification features
- The test script provides comprehensive verification of all dependencies
- These changes maintain backward compatibility with existing functionality
- Dependency tests are now automatically run as part of the standard test workflow
