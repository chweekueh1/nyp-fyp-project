# 🎭 Chatbot Demos

This directory contains interactive demonstrations of the chatbot's features and capabilities.

## 📱 Available Demos

### `demo_final_working_chatbot.py`

**Complete Feature Demonstration**

- ✅ All bug fixes implemented
- 🔍 Smart search functionality
- 🧠 Intelligent chat naming
- 🏷️ Chat renaming capabilities
- 📝 Live UI updates
- ⚡ Optimized performance

**Usage:**

```bash
python tests/demos/demo_final_working_chatbot.py
```

### `demo_enhanced_chatbot.py`

**Enhanced Features Showcase**

- 🔍 Searchable chat history
- 🧠 Smart auto-naming from first message
- 📝 Auto-updating dropdown
- 💬 Persistent conversations

**Usage:**

```bash
python tests/demos/demo_enhanced_chatbot.py
```

### `demo_chatbot_with_history.py`

**Chat History Management**

- 💾 Persistent chat sessions
- 📚 Chat history loading
- 🔄 Session switching
- 📝 Message persistence

**Usage:**

```bash
python tests/demos/demo_chatbot_with_history.py
```

### `demo_file_classification.py`

**File Classification Interface**

- 📁 File upload with validation
- 🔍 Security classification analysis
- 📊 Sensitivity level detection
- 💾 Upload history tracking

**Usage:**

```bash
python tests/demos/demo_file_classification.py
```

### `demo_enhanced_classification.py`

**Enhanced Classification System**

- 🔧 Multiple extraction methods (pandoc, tesseract OCR)
- 🎨 Beautiful response formatting with emojis
- ⚡ Performance optimization demonstrations
- 📄 Support for multiple file types
- 🔍 Dependency detection and installation guidance

**Usage:**

```bash
python tests/demos/demo_enhanced_classification.py
```

### `demo_audio_interface.py`

**Audio Input Interface**

- 🎤 Voice input functionality
- 🔊 Audio processing capabilities
- 📝 Speech-to-text conversion
- 🎵 Audio file handling

**Usage:**

```bash
python tests/demos/demo_audio_interface.py
```

## 🎯 Demo Features

### 🔍 **Smart Search**

- Search through all your chat conversations
- Intelligent keyword matching
- Context-aware results with previews
- Relevance-based ranking

### 🧠 **Intelligent Naming**

- Automatic meaningful chat names from first message
- "How do I learn Python?" → "Learn Python"
- No more generic timestamp names
- Smart keyword extraction

### 🏷️ **Chat Management**

- Rename any chat to organize conversations
- Safe filename handling with validation
- Instant UI updates
- Content preservation during rename

### 📝 **Live Updates**

- Dropdown updates automatically when creating/renaming chats
- Real-time search results
- Seamless conversation flow
- No page refreshes needed

### ⚡ **Performance**

- Optimized backend initialization
- No infinite loading loops
- Fast startup and reliable operation
- Proper error handling

## 🚀 Quick Start

1. **Choose a demo** based on what you want to test
2. **Run the demo** using the command provided
3. **Follow the on-screen instructions** for testing features
4. **Try different scenarios** to see all capabilities

## 🧪 Testing Scenarios

### For `demo_final_working_chatbot.py`

1. **Auto-Naming Test:** Type "What is machine learning?" without selecting a chat
2. **Rename Test:** Select a chat and rename it to "My ML Chat"
3. **Search Test:** Search for "machine" to find your chat
4. **Multi-Chat Test:** Create several chats and switch between them

### For `demo_enhanced_chatbot.py`

1. **Create Multiple Chats:** Try different topics (Python, JavaScript, databases)
2. **Test Search:** Search for keywords across all chats
3. **Verify Persistence:** Close and reopen to see saved conversations

### For `demo_enhanced_classification.py`

1. **Dependency Check:** See which dependencies (pandoc, tesseract) are available
2. **Content Extraction:** Test with different file types (.txt, .docx, .pdf, .png)
3. **Performance Test:** Observe processing speed with large files
4. **Formatting Demo:** See beautiful classification responses with emojis

### For `demo_file_classification.py`

1. **Upload Test:** Upload different file types and see classification
2. **History Test:** Check upload history and file management
3. **User Management:** Test with different demo usernames

### For `demo_audio_interface.py`

1. **Voice Input:** Test microphone input functionality
2. **Audio Files:** Upload and process audio files
3. **Speech Recognition:** Test speech-to-text conversion

## 📋 Demo Requirements

- Python 3.8+
- All project dependencies installed (`pip install -r requirements.txt`)
- OpenAI API key configured (for AI responses)
- Internet connection (for API calls)

## 🔧 Troubleshooting

### Common Issues

- **Port conflicts:** Demos use different ports (7865, 7866, etc.)
- **API key missing:** Set `OPENAI_API_KEY` environment variable
- **Dependencies:** Run `pip install -r requirements.txt`

### Getting Help

- Check the main project README.md
- Run the comprehensive test suite: `python tests/comprehensive_test_suite.py`
- Review error logs in the terminal output

## 📊 Demo vs Tests

**Demos** are for:

- Interactive exploration of features
- Visual verification of UI components
- Manual testing of user workflows
- Showcasing capabilities to stakeholders

**Tests** are for:

- Automated validation of functionality
- Regression testing
- Performance benchmarking
- Continuous integration

Both are important for ensuring a robust, user-friendly chatbot experience!

## 📚 Sphinx-Style Docstrings

All demo scripts and utilities in this directory use [Sphinx-style docstrings](https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#info-field-lists) for all functions, classes, and modules. This ensures:

- Consistent documentation across all demos
- Easy generation of API docs with Sphinx or similar tools
- Clear parameter and return type annotations for all contributors

**Example:**

```python
def example_demo(param1: str, param2: int) -> bool:
    """
    Brief description of what the demo function does.

    :param param1: Description of the first parameter.
    :type param1: str
    :param param2: Description of the second parameter.
    :type param2: int
    :return: Description of the return value.
    :rtype: bool
    """
    # ...
```
