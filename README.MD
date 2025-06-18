# NYP FYP CNC Chatbot

## About

The NYP-FYP CNC Chatbot is a chatbot used to help staff identify and use the
correct sensitivity labels in their communications.

It makes use of the Python programming language, along with integrations of
Gradio, Pandoc, Tesseract OCR and OpenAI

## Installation and Set-up

0. These installation instructions assumes you are installing this on Windows 10/11.

1. Git Clone the repository (Branch: **main**)

2. Install [Python Version 3.12.10](https://www.python.org/downloads/release/python-31210/)

    I. Open the installer and ensure to check the box (add to PATH) on the bottom
    of the installer screen.

3. Once done, open the cloned GitHub repository (in VS Code)

    I. Press Ctrl + Shift + P and search 'Python: Select Interpreter'.
    II. Find and select Python 3.12.10

4. Install [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

    I. After installation, run the setup executable.
    II. Run the installed Visual Studio Installer.
    III. Navigate to individal components
    IV. Select `MSVC v143 - VS 2022 C++ x64/x86 build tools (Latest)` (or its
    ARM equivalent for those using ARM)
    V. Select `Windows 11 SDK (10.0.22621.0)` (or Windows 10 SDK if you are on
    Windows 10)
    VI. Install the selected build tools (used for ChromaDB)

5. Install the library dotenv

    Open a terminal of your choice (Command Prompt, PowerShell, etc)

    ```pwsh
    python -m pip install dotenv
    ```

6. Run the setup.py

    ```pwsh
    python setup.py
    ```

    This will take a while (2 to 3 minutes).

7. Activate the virtual enviroment

    I. Press Ctrl + Shift + P and search 'Python: Select Interpreter'.
    II. Find and select Python 3.12.10 ('.venv')

    ```pwsh
    .venv\Scripts\activate
    ```

## Running the Model Interface (Frontend & Backend)

Run gradio_app.py

```pwsh
python gradio_app.py
```

This will take a while to start up (10 to 30 seconds), as it has to
compile the `langchain` dependencies unless there is already a cached instance.

## Environment Variables

To run this project, copy over the contents of `.env.dev` to a new `.env` file.

In addition, you will need to add the following environment variable to
your .env file.

`OPENAI_API_KEY`: Your OpenAI API key.

___

## Testing

The project includes two test files:

1. `tests/run_tests.py` - Basic environment tests
   - Tests environment variables
   - Tests required directories and files
   - Tests module imports
   - Tests CSS file validity
   - Run with: `python tests/run_tests.py`

2. `tests/run_all_tests.py` - Comprehensive test suite
   - Discovers and runs all test modules in the tests directory
   - Creates detailed logs in the `logs` directory
   - Provides more verbose output
   - Run with: `python tests/run_all_tests.py`

### When to Use Which Test File

- Use `run_tests.py` when you want to quickly verify the basic environment setup
- Use `run_all_tests.py` when you want to run the complete test suite with detailed logging

### Test Logs

Test logs are stored in the `logs` directory with timestamps in the format: `test_run_YYYYMMDD_HHMMSS.log`
