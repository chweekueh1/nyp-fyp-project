# Frontend Test Suite

This directory contains comprehensive tests for the Gradio-based frontend components of the NYP FYP CNC Chatbot application.

## Test Structure

### Component Tests
- **`test_login_ui.py`** - Login and registration interface tests
- **`test_chat_ui.py`** - Chat interface and chatbot tests
- **`test_search_ui.py`** - Search interface and chat history tests
- **`test_file_audio_ui.py`** - File upload and audio input tests
- **`test_all_interfaces.py`** - Combined interface test

### Enhanced State Interaction Tests
- **`test_ui_state_interactions.py`** - **NEW!** Comprehensive tests for UI state interactions, component behavior, and user flows

## Test Categories

### 1. Component Creation Tests (Legacy)
These tests verify that UI components can be created without errors:
- Login interface creation
- Chat interface creation
- Search interface creation
- File upload interface creation
- Audio input interface creation

### 2. Enhanced State Interaction Tests (NEW!)
These tests validate actual UI behavior and state management:

#### Login State Propagation
- Tests that login state properly propagates to other components
- Validates successful and failed login flows
- Ensures proper visibility changes for containers and buttons

#### Chat Interface State Updates
- Tests message handling and state updates
- Validates chat history management
- Ensures proper error handling for empty messages and unauthorized access

#### Component Interactions
- Tests how components interact with each other
- Validates complete user flows from login to logout
- Ensures state consistency across component boundaries

#### Search Interface Integration
- Tests search functionality with different login states
- Validates command handling (e.g., `/help`)
- Ensures proper integration with chat history

#### File Upload State Management
- Tests file upload visibility based on login state
- Validates proper state integration

#### Audio Input State Management
- Tests audio input visibility based on login state
- Validates proper state integration

## Running Tests

### Run All Frontend Tests
```bash
# From project root
python tests/frontend/run_frontend_tests.py test

# Or from frontend directory
cd tests/frontend
python run_frontend_tests.py test
```

### Run Specific Test Categories
```bash
# Run only component creation tests
python tests/frontend/run_frontend_tests.py test --test login
python tests/frontend/run_frontend_tests.py test --test chat
python tests/frontend/run_frontend_tests.py test --test search
python tests/frontend/run_frontend_tests.py test --test file-upload

# Run enhanced state interaction tests
python tests/frontend/run_frontend_tests.py test --test ui-state
```

### Launch Test Apps for Manual Testing
```bash
# Launch specific test apps
python tests/frontend/run_frontend_tests.py launch --test login
python tests/frontend/run_frontend_tests.py launch --test chat
python tests/frontend/run_frontend_tests.py launch --test all
```

## Available Tests

### Login Tests
- **Simple Login**: Basic login functionality with test credentials
- **Full Login**: Complete login interface with registration and password toggle

### Chat Tests
- **Chat Interface**: Basic chat functionality with message sending
- **Chatbot Interface**: Advanced chatbot with response generation

### Search Tests
- **Search Interface**: Search functionality with mock results
- **Chat History**: Chat history management and navigation

### File/Audio Tests
- **File Upload**: File upload and processing interface
- **Audio Input**: Audio recording and processing interface

### Comprehensive Test
- **All Interfaces**: All interfaces combined in a tabbed interface

## Test Credentials

All tests use the following mock credentials:
- **Username**: `test`
- **Password**: `test`

## Test Features

### Mock Data
- All tests use mock data to avoid backend dependencies
- No files are created or modified during testing
- Mock responses are generated for all user interactions

### State Management
- Proper Gradio state management for all components
- Consistent state updates across all interfaces
- Error handling and validation testing

### UI Responsiveness
- Button click testing
- Form validation testing
- Error message display testing
- Component visibility testing

## Running Individual Tests

You can also run individual test files directly:

```bash
# Run login tests
python tests/frontend/test_login_ui.py

# Run chat tests
python tests/frontend/test_chat_ui.py

# Run search tests
python tests/frontend/test_search_ui.py

# Run file/audio tests
python tests/frontend/test_file_audio_ui.py

# Run comprehensive test
python tests/frontend/test_all_interfaces.py
```

## Test Output

### Console Output
- Test creation status
- Button click events (when debug prints are enabled)
- Error messages and validation feedback

### Gradio Interface
- Interactive UI for manual testing
- Real-time feedback for all user actions
- Visual confirmation of component functionality

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the parent directory is in the Python path
2. **Button Non-Responsiveness**: Check console for debug output
3. **State Issues**: Verify state variables are properly initialized

### Debug Mode
All test apps launch with `debug=True` to provide detailed error information.

## Contributing

When adding new UI components:

1. Create a corresponding test file in this directory
2. Add the test to the main test runner
3. Include both individual and comprehensive tests
4. Use mock data to avoid backend dependencies
5. Add proper error handling and validation testing 