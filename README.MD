# NYP FYP CNC Chatbot

A Gradio-based Python chatbot application designed to help staff identify and use the correct sensitivity labels in their communications. The application features login, registration, chat, and search functionalities.

## About

The NYP-FYP CNC Chatbot is a chatbot used to help staff identify and use the correct sensitivity labels in their communications. It makes use of the Python programming language, along with integrations of Gradio, Pandoc, Tesseract OCR and OpenAI.

## 🚀 Quick Start

### Prerequisites

- Python 3.12.10 or higher
- Git
- OpenAI API key
- Windows 10/11 (for full functionality)
- Microsoft Visual C++ Build Tools (for ChromaDB)

### Installation

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd nyp-fyp-project
   ```

2. Install [Python Version 3.12.10](https://www.python.org/downloads/release/python-31210/)
   
   **Important**: Open the installer and ensure to check the box (add to PATH) on the bottom of the installer screen.

3. Install [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   
   **Required for ChromaDB functionality:**
   - After installation, run the setup executable
   - Run the installed Visual Studio Installer
   - Navigate to individual components
   - Select `MSVC v143 - VS 2022 C++ x64/x86 build tools (Latest)` (or its ARM equivalent for those using ARM)
   - Select `Windows 11 SDK (10.0.22621.0)` (or Windows 10 SDK if you are on Windows 10)
   - Install the selected build tools

4. Create a virtual environment
   ```bash
   python -m venv .venv
   ```

5. Activate the virtual environment
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

6. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

7. Set up environment variables
   ```bash
   # Copy the development environment template
   cp .env.dev .env
   
   # Edit .env and add your OpenAI API key
   # OPENAI_API_KEY=your_openai_api_key_here
   ```

8. Run the setup script
   ```bash
   python setup.py
   ```
   
   This will take a while (2 to 3 minutes) as it sets up all required dependencies including Pandoc and Tesseract OCR.

## 🏃‍♂️ Running the Application

### Start the Application

**⚠️ Important**: Make sure your virtual environment is activated before running the application.

```bash
# Activate virtual environment (if not already activated)
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Start the application
python app.py
```

The application will be available at `http://localhost:7860` (or the URL shown in the terminal).

**Note**: This will take a while to start up (10 to 30 seconds), as it has to compile the `langchain` dependencies unless there is already a cached instance.

### Development Mode
```bash
# Make sure virtual environment is activated
python app.py --debug
```

## 🔧 Environment Variables

The application uses environment variables for configuration. Copy the contents of `.env.dev` to create your own `.env` file:

```bash
cp .env.dev .env
```

### Required Environment Variables

Edit your `.env` file and add the following variables:

```bash
# Copy over and create your own .env file

DEPENDENCIES_PATH = dependencies\poppler-25.03.0;dependencies\tesseract-ocr-5.5.0.20241111;dependencies\pandoc-3.6.4
CHAT_DATA_PATH = data\modelling\data\
CLASSIFICATION_DATA_PATH = data\modelling\CNC chatbot\data classification\
DATABASE_PATH=data\vector_store\chroma_db\
LANGCHAIN_CHECKPOINT_PATH = data\memory_persistence\checkpoint.sqlite3
KEYWORDS_DATABANK_PATH = data\keyword\keywords_databank
CHAT_SESSIONS_PATH = data\chat_sessions\
EMBEDDING_MODEL = text-embedding-3-small
OPENAI_API_KEY = add_your_own_api_key 
```

### Getting Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in or create an account
3. Navigate to "API Keys" in your dashboard
4. Click "Create new secret key"
5. Copy the key and add it to your `.env` file

**⚠️ Important**: Never commit your `.env` file to version control. It's already included in `.gitignore`.

## 🧪 Testing

The project includes a comprehensive, organized test suite with automated runners and interactive demos.

### 🚀 Quick Test Commands

**⚠️ Important**: Make sure your virtual environment is activated before running tests.

```bash
# Activate virtual environment (if not already activated)
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Run comprehensive test suite (recommended)
python tests/comprehensive_test_suite.py

# Run legacy test runners
python tests/run_all_tests.py
python tests/run_tests.py
```

### 🎭 Interactive Demos

Experience the chatbot features with interactive demonstrations:

```bash
# Complete working chatbot demo (all features)
python tests/demos/demo_final_working_chatbot.py

# Enhanced features showcase
python tests/demos/demo_enhanced_chatbot.py

# Chat history management demo
python tests/demos/demo_chatbot_with_history.py

# File classification interface demo
python tests/demos/demo_file_classification.py

# Enhanced classification system demo
python tests/demos/demo_enhanced_classification.py

# Audio input interface demo
python tests/demos/demo_audio_interface.py
```

**📋 Demo Features:**
- **Chatbot Demos**: Complete chat interface with history, search, and smart naming
- **File Classification**: Upload and classify documents with security analysis
- **Enhanced Classification**: Advanced file processing with pandoc and OCR
- **Audio Interface**: Voice input, transcription, and audio file processing

### 📁 Organized Test Structure

- **`tests/backend/`** - Backend component tests (API, database, core logic)
- **`tests/frontend/`** - UI component tests (login, chat, search interfaces)
- **`tests/integration/`** - Feature integration and end-to-end tests
- **`tests/llm/`** - Language model and AI functionality tests
- **`tests/demos/`** - Interactive demonstrations and showcases
- **`tests/utils/`** - Testing utilities and diagnostic tools

### 🎯 Test Categories

- **Unit Tests**: Individual component testing in isolation
- **Integration Tests**: Component interaction and workflow testing
- **Frontend Tests**: UI components, user interactions, state management
- **Demo Tests**: Interactive feature demonstrations and user experience validation

For detailed testing information, see [tests/README.md](tests/README.md).

## 📋 Test Execution Options

### Comprehensive Test Suite (Recommended)

The main test runner provides organized execution of all test categories:

```bash
# Run complete test suite with detailed reporting
python tests/comprehensive_test_suite.py
```

**Features:**
- Organized test execution by category (unit, integration, frontend)
- Detailed timing and success rate reporting
- Automatic discovery of available demos
- Comprehensive summary with actionable results

### Individual Test Categories

Run specific test categories when working on particular components:

```bash
# Backend tests (API, database, core logic)
python tests/backend/test_backend.py
python tests/backend/test_backend_fixes_and_rename.py

# Frontend tests (UI components, interactions)
python tests/frontend/test_ui_fixes.py
python tests/frontend/test_login_ui.py
python tests/frontend/run_frontend_tests.py

# Integration tests (end-to-end workflows)
python tests/integration/test_enhanced_chatbot_features.py
python tests/integration/test_improved_app.py

# LLM tests (AI functionality)
python tests/llm/test_llm.py
```

### Legacy Test Runners

For compatibility, the original test runners are still available:

```bash
# Legacy comprehensive runner
python tests/run_all_tests.py

# Environment validation
python tests/run_tests.py

# Frontend-specific runner
python tests/frontend/run_frontend_tests.py test
```

### Test Coverage

The test suite covers:

- **Frontend (UI Components)**: Login, registration, chat interface, search interface, file upload, audio input, chatbot, and chat history
- **Backend (API & Logic)**: Authentication, chat management, data processing, rate limiting, error handling, and utility functions
- **LLM Services**: Chat model, classification, data processing, model caching, and backward compatibility
- **Integration**: End-to-end testing with real API calls and file operations
- **Environment**: Environment variables, file existence, and module imports

### Test Results

Each test suite provides:
- ✅ PASSED/❌ FAILED status for each test
- Detailed error messages for failed tests
- Summary statistics (passed/failed counts)
- Total execution time
- Comprehensive final summary

### When to Use Which Test

- **`run_all_tests.py`**: Use for complete testing before deployment or major changes
- **Frontend tests**: Use when making UI changes or adding new components
- **Backend tests**: Use when modifying API endpoints or business logic
- **LLM tests**: Use when updating LLM services or models
- **Integration tests**: Use for integration testing with live backend
- **Environment tests**: Use for quick environment validation

### Test Credentials

For frontend testing, use these mock credentials:
- **Username:** `test`
- **Password:** `test`

### Test Logs

Test logs are stored in the `app.log` file with timestamps and detailed information about test execution.

## 📁 Project Structure

```
nyp-fyp-project/
├── app.py                 # Main application entry point
├── backend.py             # Backend API and business logic
├── utils.py               # Utility functions
├── gradio_modules/        # UI components
│   ├── login_and_register.py  # Authentication interface
│   ├── chatbot.py             # Enhanced chatbot interface
│   ├── file_classification.py # File upload & classification
│   ├── audio_input.py         # Audio input interface
│   ├── chat_interface.py      # Legacy (tests only)
│   ├── search_interface.py    # Legacy (tests only)
│   ├── chat_history.py        # Legacy (tests only)
│   └── file_upload.py         # Legacy (tests only)
├── llm/                   # Language model services
├── styles/                # CSS and theming
├── scripts/               # JavaScript and client-side code
├── tests/                 # Test suite
```

## 📊 Features

- **Sensitivity Label Assistance**: Help staff identify and use correct sensitivity labels
- **User Authentication**: Login and registration system
- **Chat Interface**: Real-time chat with AI assistant
- **Search Functionality**: Search through chat history
- **File Upload**: Support for document upload and processing (PDF, DOCX, etc.)
- **Audio Input**: Voice-to-text functionality
- **Chat History**: Persistent chat sessions
- **Global Search**: Command-based navigation and search
- **OCR Integration**: Text extraction from images using Tesseract
- **Document Processing**: Support for various document formats via Pandoc

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're in the correct directory
   - Activate the virtual environment
   - Check that all dependencies are installed

2. **API Key Issues**
   - Verify your OpenAI API key is correct
   - Check that the `.env` file exists and is properly formatted
   - Ensure the API key has sufficient credits

3. **Port Conflicts**
   - The default port is 7860
   - If occupied, Gradio will automatically use the next available port

4. **Environment Variables**
   - Check the `.env` file if using one
   - Ensure all required variables are set

5. **Visual C++ Build Tools**
   - Required for ChromaDB functionality
   - Install the latest MSVC build tools if you encounter compilation errors

6. **Dependencies**
   - Ensure Pandoc and Tesseract OCR are properly installed
   - Check that all PATH variables are correctly set

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.