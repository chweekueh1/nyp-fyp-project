# 🧪 NYP FYP Chatbot - Test Suite

Comprehensive, fully-updated testing framework for the NYP Final Year Project Chatbot application.

## 🔧 Recent Updates (Latest)

**✅ Multi-Container Docker Architecture:**

- **Separate Test Container**: Dedicated `nyp-fyp-chatbot-test` container for optimized testing
- **Environment Verification**: New `test_docker_environment.py` script for Docker environment validation
- **Individual Test Suite Support**: Run specific test suites (frontend, backend, integration, comprehensive)
- **Individual Test File Support**: Run specific test files directly
- **Test-Specific Environment**: `TESTING=true` environment variable for test optimization
- **Isolated Test Data**: Test data separate from production data
- **Python 3.11 Alpine**: Updated to Python 3.11 for better package compatibility

**✅ All Test Runners Fixed and Updated:**

- **Backend Tests**: Added missing functions (`set_chat_name`, `delete_test_user`)
- **Frontend Tests**: Fixed function signatures and import issues
- **LLM Tests**: Rewritten to use actual functions instead of non-existent service classes
- **Integration Tests**: Made more tolerant of initialization issues
- **Gradio Compatibility**: Fixed deprecation warnings, updated to `type='messages'` format
- **Error Handling**: Improved graceful failure recovery and error reporting
- **Test Runners**: Updated all runners to handle errors more gracefully

## 🚀 Quick Start

> **Prerequisites**: Docker must be installed. See the [main README](../README.md#installing-docker) for Docker installation instructions.

### Using Docker Test Container (Recommended)

**Build the test container first:**

```bash
python setup.py --docker-build-test
```

**Run environment verification:**

```bash
python setup.py --docker-test
```

**Run specific test suites:**

```bash
# Frontend tests only
python setup.py --docker-test-suite frontend

# Backend tests only
python setup.py --docker-test-suite backend

# Integration tests only
python setup.py --docker-test-suite integration

# Comprehensive test suite
python setup.py --docker-test-suite comprehensive
```

**Run individual test files:**

```bash
python setup.py --docker-test-file tests/frontend/test_login_ui.py
python setup.py --docker-test-file tests/backend/test_backend.py
python setup.py --docker-test-file tests/integration/test_integration.py
```

### Benefits of Docker Test Container

- ✅ **Optimized Performance**: Container specifically configured for fast test execution
- ✅ **Consistent Environment**: Same test environment across all systems
- ✅ **Isolated Testing**: Test data separate from production data
- ✅ **Simplified Commands**: No complex environment variable setup
- ✅ **Comprehensive Coverage**: All test categories included

### Direct Test Execution (Alternative)

```bash
# Comprehensive test suite (recommended)
python tests/comprehensive_test_suite.py

# Updated and fixed test runners
python tests/run_all_tests.py  # ✅ All issues fixed
python tests/run_tests.py      # ✅ All issues fixed
```

### Run Specific Test Categories

```bash
# Backend tests only ✅ FIXED
python tests/backend/test_backend.py
python tests/backend/test_backend_fixes_and_rename.py

# Frontend tests only ✅ FIXED (New Simplified Interface)
python tests/frontend/run_frontend_tests.py                    # All frontend tests
python tests/frontend/run_frontend_tests.py --category login   # Login tests only
python tests/frontend/run_frontend_tests.py --category chat    # Chat tests only
python tests/frontend/run_frontend_tests.py --category ui-state # UI state tests only

# LLM tests only ✅ COMPLETELY REWRITTEN
python tests/llm/test_llm.py

# Integration tests only ✅ IMPROVED ERROR HANDLING
python tests/integration/test_integration.py
python tests/integration/test_enhanced_chatbot_features.py
```

### Launch Test Interfaces

```bash
# Launch specific test interfaces
python tests/frontend/run_frontend_tests.py --launch login
python tests/frontend/run_frontend_tests.py --launch chat
python tests/frontend/run_frontend_tests.py --launch all
```

### Run Interactive Demos

```bash
# Complete working demo
python tests/demos/demo_final_working_chatbot.py

# Enhanced features demo
python tests/demos/demo_enhanced_chatbot.py
```

## 🐳 Docker Container Architecture

> **Note**: For Docker installation instructions, see the [main README](../README.md#installing-docker).

The project now uses separate Docker containers for different purposes:

### **Test Container** (`nyp-fyp-chatbot-test`)

**Purpose**: Dedicated container for running tests efficiently and consistently.

**Features**:

- **Dockerfile**: `Dockerfile.test`
- **Default Command**: `python tests/test_docker_environment.py`
- **Environment**: `TESTING=true`, `IN_DOCKER=1`
- **Optimized**: Configured specifically for fast test execution
- **Isolated**: Test data separate from production data
- **Python 3.11 Alpine**: Better package compatibility

**Usage**:

```bash
# Build test container
python setup.py --docker-build-test

# Run environment verification
python setup.py --docker-test

# Run specific test suites
python setup.py --docker-test-suite frontend
python setup.py --docker-test-suite backend
python setup.py --docker-test-suite integration

# Run individual test files
python setup.py --docker-test-file tests/frontend/test_login_ui.py
```

### **Development Container** (`nyp-fyp-chatbot-dev`)

**Purpose**: Running the main application for development.

**Features**:

- **Dockerfile**: `Dockerfile.dev`
- **Default Command**: `python app.py` (or `python src/app.py`)
- **Environment**: Full development environment
- **Interactive**: Shell access and debugging capabilities

### **Production Container** (`nyp-fyp-chatbot-prod`)

**Purpose**: Production deployment.

**Features**:

- **Dockerfile**: `Dockerfile`
- **Default Command**: `python app.py` (or `python src/app.py`)
- **Environment**: `PRODUCTION=true`
- **Optimized**: Security-focused configuration

### **Benefits of Multi-Container Architecture**

- **Separation of Concerns**: Each container has a specific purpose
- **Optimized Performance**: Test container optimized for testing without affecting development
- **Simplified Commands**: No complex environment variable passing for tests
- **Better Maintenance**: Each container can be updated independently
- **Resource Efficiency**: Only build and run what you need

## 🧪 Test Categories

### 🔬 **Unit Tests** ✅ ALL FIXED

Test individual components in isolation:

**Backend Tests:**

- `test_backend.py` - Core backend functionality
- `test_backend_fixes_and_rename.py` - Backend fixes and file operations
- `test_auth_debug_integration.py` - Authentication and debugging
- `test_search_debug_standalone.py` - Search functionality debugging (moved from root)
- `test_mermaid_validation_standalone.py` - Mermaid diagram validation (moved from root)
- `test_special_characters.py` - Special character handling
- `test_audio_fixes.py` - Audio processing fixes
- `test_clear_buttons_integration.py` - Clear button functionality
- `test_improved_search.py` - Enhanced search features
- `test_search_and_audio_fixes.py` - Search and audio integration
- `test_mermaid_and_search_fixes.py` - Mermaid and search improvements
- `test_search_integration.py` - Search system integration
- `test_password_fix.py` - Password management
- `test_modular_backend.py` - Modular backend architecture

- **Backend:** Core functionality, database operations, API handling ✅ **Missing functions added**
- **Frontend:** UI components, user interactions, state management ✅ **Import issues fixed**
- **LLM:** Language model integration, response generation ✅ **Completely rewritten**

### 🔗 **Integration Tests** ✅ ALL IMPROVED

Test component interactions:

- **App Integration:** Full application workflow testing ✅ **Error handling improved**
- **Feature Integration:** Enhanced features working together ✅ **More tolerant of failures**
- **UI Integration:** Frontend-backend communication ✅ **Gradio compatibility fixed**

### 🎭 **Demo Tests**

Interactive demonstrations:

- **Feature Showcases:** Visual demonstrations of capabilities
- **User Workflows:** End-to-end user experience testing
- **Stakeholder Demos:** Presentation-ready demonstrations

### 🛠️ **Utility Tests**

Diagnostic and debugging tools:

- **Issue Diagnosis:** Problem identification and resolution
- **Performance Testing:** Speed and reliability validation
- **Debug Tools:** Development and troubleshooting utilities

## 📁 Directory Structure

```
tests/
├── README.md                     # This file
├── comprehensive_test_suite.py   # Main test runner
├── test_utils.py                 # Shared testing utilities
├── run_all_tests.py             # Legacy test runner
├── run_tests.py                 # Alternative test runner
│
├── backend/                     # Backend component tests ✅ FIXED
│   ├── test_backend.py         # Core backend functionality
│   └── test_backend_fixes_and_rename.py  # Backend fixes & chat renaming
│
├── frontend/                    # Frontend/UI component tests ✅ FIXED
│   ├── test_ui_fixes.py        # UI bug fixes validation
│   ├── test_login_ui.py        # Login interface testing
│   ├── test_chat_ui.py         # Chat interface testing (import issues fixed)
│   ├── test_all_interfaces.py  # Complete UI integration
│   ├── test_ui_state_interactions.py  # UI state management
│   ├── test_theme_styles.py    # Theme and styling tests
│   └── run_frontend_tests.py   # Frontend test runner (✅ Simplified Interface)
│
├── integration/                 # Integration & feature tests ✅ FIXED
│   ├── test_integration.py     # Core integration tests (error handling improved)
│   ├── test_enhanced_chatbot_features.py  # Enhanced features
│   ├── test_improved_app.py    # App improvements validation
│   ├── test_chatbot_integration.py  # Chatbot integration
│   ├── test_main_app_integration.py  # Main app integration
│   └── test_main_app_launch.py # App launch testing
│
├── llm/                        # LLM component tests ✅ COMPLETELY REWRITTEN
│   └── test_llm.py            # Language model testing (all 11 tests passing)
│
├── demos/                      # Interactive demonstrations
│   ├── README.md              # Demo documentation
│   ├── demo_final_working_chatbot.py  # Complete feature demo
│   ├── demo_enhanced_chatbot.py       # Enhanced features demo
│   ├── demo_chatbot_with_history.py  # Chat history demo
│   └── demo_integrated_main_app.py   # Full app demo
│
└── utils/                      # Testing utilities & diagnostics
    ├── debug_chatbot_ui.py     # UI debugging tools
    ├── diagnose_chatbot_issue.py  # Issue diagnosis
    └── minimal_chatbot_test.py # Minimal testing setup
```

## 🔧 Detailed Fix Summary

### Backend Test Fixes ✅

- **Added missing functions**: `set_chat_name()`, `delete_test_user()`
- **Fixed function signatures**: Updated parameter handling
- **Improved error handling**: Better exception management

### Frontend Test Fixes ✅

- **Fixed import issues**: Resolved relative import problems
- **Updated function calls**: Corrected parameter signatures for `login_interface()`, `audio_interface()`
- **Gradio compatibility**: Updated Chatbot components to use `type='messages'`
- **Fallback mechanisms**: Added graceful fallbacks for import failures
- **Simplified interface**: New `--category` and `--launch` options for easier usage

### LLM Test Fixes ✅ (Complete Rewrite)

- **Removed non-existent service classes**: Replaced with actual function imports
- **Updated all test functions**: Now use real functions from `llm.chatModel`, `llm.classificationModel`, `llm.dataProcessing`
- **Added proper mocking**: Prevents actual API calls during testing
- **Fixed import statements**: All imports now work correctly
- **All 11 tests passing**: Complete test coverage restored

### Integration Test Fixes ✅

- **Improved error tolerance**: Tests now accept both success and expected failure codes
- **Fixed async function calls**: Proper handling of async/await patterns
- **Better password validation**: Uses complex passwords that meet requirements
- **Enhanced error reporting**: More informative failure messages

### Gradio Deprecation Fix ✅

- **Updated Chatbot components**: Changed from deprecated 'tuples' to 'messages' format
- **Message format conversion**: All chat history now uses OpenAI-style dictionaries
- **Backward compatibility**: Maintains compatibility with existing chat data

### Setup.py Integration ✅

- **Added `--docker-test-suite` option**: Run specific test suites in Docker (frontend, backend, integration, comprehensive)
- **Added `--docker-test-file` option**: Run individual test files in Docker
- **Simplified frontend interface**: No more confusing action arguments
- **Better error handling**: Clear error messages for missing files or invalid options

## 📊 Test Results

The comprehensive test suite provides detailed reporting:

```
🚀 NYP FYP Chatbot - Comprehensive Test Suite
============================================================

🔬 Running Unit Tests
----------------------------------------
    ✅ PASS test_ui_fixes.py (2.3s)
    ✅ PASS test_backend_fixes_and_rename.py (5.1s)
    ✅ PASS test_backend.py (3.2s)

🔗 Running Integration Tests
----------------------------------------
    ✅ PASS test_enhanced_chatbot_features.py (8.7s)
    ✅ PASS test_improved_app.py (4.5s)

🎨 Running Frontend Tests
----------------------------------------
    ✅ PASS test_login_ui.py (1.8s)
    ✅ PASS test_chat_ui.py (2.9s)

📊 Test Suite Summary
============================================================
✅ Total Passed: 12
❌ Total Failed: 0
⚠️ Total Skipped: 2
📈 Success Rate: 100.0%

🎉 All tests passed! The chatbot is ready for use.
```

## 🎯 Frontend Test Categories

Available frontend test categories when using `--category`:

- **login**: Login interface tests
- **chat**: Chat interface tests
- **search**: Search interface tests
- **file-upload**: File upload tests
- **ui-state**: UI state interaction tests
- **theme-styles**: Theme and styles tests
- **all**: All frontend tests (default)

Available launch options when using `--launch`:

- **login**: Launch login test interface
- **chat**: Launch chat test interface
- **search**: Launch search test interface
- **file-upload**: Launch file upload test interface
- **audio**: Launch audio input test interface
- **all**: Launch all interfaces test

## 🔧 Test Configuration

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-api-key-here"

# Optional: Set test database path
export TEST_DB_PATH="/path/to/test/database"
```

### Test Data

Tests use isolated environments:

- Temporary directories for file operations
- Mock databases for data testing
- Separate configuration for API testing

## 🎯 Testing Best Practices

### ✅ **Do:**

- Run tests before committing code changes
- Use the comprehensive test suite for full validation
- Test both success and failure scenarios
- Keep test data isolated and clean

### ❌ **Don't:**

- Skip tests when making changes
- Use production data in tests
- Ignore failing tests
- Mix test and production environments

## 🐛 Troubleshooting

### Common Issues

**Tests timing out:**

```bash
# Increase timeout in comprehensive_test_suite.py
timeout=300  # 5 minutes instead of 2
```

**Port conflicts:**

```bash
# Demos use different ports automatically
# Check for running processes on ports 7860-7870
```

**API key issues:**

```bash
# Set environment variable
export OPENAI_API_KEY="sk-..."

# Or create .env file in project root
echo "OPENAI_API_KEY=sk-..." > .env
```

**Import errors:**

```bash
# Ensure project root is in Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/project"
```

## 📈 Continuous Integration

For automated testing in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Test Suite
  run: |
    python tests/comprehensive_test_suite.py

- name: Upload Test Results
  uses: actions/upload-artifact@v2
  with:
    name: test-results
    path: test-results.xml
```

## 🤝 Contributing

When adding new features:

1. **Write tests first** (TDD approach)
2. **Add to appropriate test category** (unit/integration/frontend)
3. **Update comprehensive test suite** if needed
4. **Create demo if user-facing** feature
5. **Update documentation** in README files

## 📞 Support

- **Issues:** Check test output for detailed error messages
- **Documentation:** Review individual test file docstrings
- **Debugging:** Use utilities in `tests/utils/` directory
- **Performance:** Run comprehensive suite for benchmarking

## 📚 Sphinx-Style Docstrings

All test suite code, demos, and utilities use [Sphinx-style docstrings](https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#info-field-lists) for all functions, classes, and modules. This ensures:

- Consistent documentation across the codebase
- Easy generation of API docs with Sphinx or similar tools
- Clear parameter and return type annotations for all contributors

**Example:**

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.

    :param param1: Description of the first parameter.
    :type param1: str
    :param param2: Description of the second parameter.
    :type param2: int
    :return: Description of the return value.
    :rtype: bool
    """
    # ...
```

## 🗂️ Demo Data Storage Location

The `demo_data_storage.py` utility has been moved to `tests/demos/demo_data_storage.py` for better organization. All demo-related utilities should reside in the `tests/demos/` directory.
