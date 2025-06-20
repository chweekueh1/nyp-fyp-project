# 🧪 NYP FYP Chatbot - Test Suite

Comprehensive testing framework for the NYP Final Year Project Chatbot application.

## 📁 Directory Structure

```
tests/
├── README.md                     # This file
├── comprehensive_test_suite.py   # Main test runner
├── test_utils.py                 # Shared testing utilities
├── run_all_tests.py             # Legacy test runner
├── run_tests.py                 # Alternative test runner
│
├── backend/                     # Backend component tests
│   ├── test_backend.py         # Core backend functionality
│   └── test_backend_fixes_and_rename.py  # Backend fixes & chat renaming
│
├── frontend/                    # Frontend/UI component tests
│   ├── test_ui_fixes.py        # UI bug fixes validation
│   ├── test_login_ui.py        # Login interface testing
│   ├── test_chat_ui.py         # Chat interface testing
│   ├── test_all_interfaces.py  # Complete UI integration
│   └── run_frontend_tests.py   # Frontend test runner
│
├── integration/                 # Integration & feature tests
│   ├── test_integration.py     # Core integration tests
│   ├── test_enhanced_chatbot_features.py  # Enhanced features
│   ├── test_improved_app.py    # App improvements validation
│   ├── test_chatbot_integration.py  # Chatbot integration
│   ├── test_main_app_integration.py  # Main app integration
│   └── test_main_app_launch.py # App launch testing
│
├── llm/                        # LLM component tests
│   └── test_llm.py            # Language model testing
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

## 🚀 Quick Start

### Run All Tests
```bash
# Comprehensive test suite (recommended)
python tests/comprehensive_test_suite.py

# Alternative runners
python tests/run_all_tests.py
python tests/run_tests.py
```

### Run Specific Test Categories
```bash
# Backend tests only
python tests/backend/test_backend.py
python tests/backend/test_backend_fixes_and_rename.py

# Frontend tests only
python tests/frontend/run_frontend_tests.py

# Integration tests only
python tests/integration/test_enhanced_chatbot_features.py
```

### Run Interactive Demos
```bash
# Complete working demo
python tests/demos/demo_final_working_chatbot.py

# Enhanced features demo
python tests/demos/demo_enhanced_chatbot.py
```

## 🧪 Test Categories

### 🔬 **Unit Tests**
Test individual components in isolation:
- **Backend:** Core functionality, database operations, API handling
- **Frontend:** UI components, user interactions, state management
- **LLM:** Language model integration, response generation

### 🔗 **Integration Tests**
Test component interactions:
- **App Integration:** Full application workflow testing
- **Feature Integration:** Enhanced features working together
- **UI Integration:** Frontend-backend communication

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

### Common Issues:

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
