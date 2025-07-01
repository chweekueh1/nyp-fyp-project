# NYP FYP CNC Chatbot

A Gradio-based Python chatbot application designed to help staff identify and use the correct sensitivity labels in their communications. The application features login, registration, chat, and search functionalities.

---

## About

The NYP-FYP CNC Chatbot is a chatbot used to help staff identify and use the correct sensitivity labels in their communications. It makes use of the Python programming language, along with integrations of Gradio, Pandoc, Tesseract OCR and OpenAI.

---

> **Recommended:** Use Docker for the easiest and most reliable setup. See the Docker Usage section below. The `setup.py` script is only needed for advanced local development outside Docker.

## 🚀 Quick Start

### Prerequisites

  * **Python 3.12.0 or higher**: Ensure you have a compatible Python version installed.
  * **Git**: Required for cloning the repository.
  * **OpenAI API key**: Necessary for AI functionalities.
  * **Compiler Tools**:
      * **Windows**: Microsoft Visual C++ Build Tools are required for certain Python packages (like ChromaDB) that need to compile C/C++ extensions.
      * **Linux**: While Python's `pip` generally handles compilation on Linux if standard build tools are available, you might need to install `build-essential` (Debian/Ubuntu) or `base-devel` (Arch Linux) if you encounter compilation errors for specific packages.

### Installation

1.  **Clone the repository**

    ```bash
    git clone <repository-url>
    cd nyp-fyp-project
    ```

2.  **Install Python Version 3.12.0 (if you don't have it)**

      * **Windows**: You can download it from [Python.org](https://www.python.org/downloads/release/python-31210/). During installation, make sure to **check the box "Add python.exe to PATH"**.
      * **Linux**: It's recommended to install Python via your distribution's package manager (e.g., `sudo apt install python3.12` on Debian/Ubuntu, `sudo pacman -S python` on Arch Linux) or using a version manager like `pyenv`.

3.  **Install Compiler Tools (if prompted or encountering errors)**

      * **Windows (Microsoft Visual C++ Build Tools)**:
          * Download from [visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
          * After installation, run the setup executable and then the **Visual Studio Installer**.
          * Navigate to **Individual components**.
          * Select `MSVC v143 - VS 2022 C++ x64/x86 build tools (Latest)` (or its ARM equivalent).
          * Select `Windows 11 SDK (10.0.22621.0)` (or the appropriate Windows 10 SDK).
          * Install the selected components.
      * **Linux**: If you encounter compilation errors during `pip install`, you might need to install development tools. For example:
          * Debian/Ubuntu: `sudo apt install build-essential python3-dev`
          * Arch Linux: `sudo pacman -S base-devel python` (usually part of base installation)

4.  **The rest of the installation is handled by the setup script. Proceed to step 7!**
    (The setup script will create and manage the virtual environment, install Python dependencies, and set up Pandoc/Tesseract.)

5.  **Set up environment variables**

    ```bash
    # Copy the development environment template
    cp .env.dev .env

    # Edit .env and add your OpenAI API key
    # OPENAI_API_KEY=your_openai_api_key_here
    ```

6.  **Run the setup script**

    ```bash
    python setup.py
    ```

    This will take a while (2 to 3 minutes) as it sets up all required dependencies, including creating a virtual environment, installing Python packages, and configuring Pandoc and Tesseract OCR.

---

## 🐳 Installing Docker

Docker is required to build and run the application in a containerized environment. Follow the instructions for your platform:

### Linux
- **Recommended:** Use your distribution's package manager or the official Docker installation script.
- Official instructions: https://docs.docker.com/engine/install/
- Example for Ubuntu:
  ```bash
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl gnupg
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo systemctl enable --now docker
  sudo usermod -aG docker $USER
  # Log out and back in for group changes to take effect
  ```

### macOS
- Download and install Docker Desktop: https://www.docker.com/products/docker-desktop/
- After installation, start Docker Desktop from Applications.

### Windows
- Download and install Docker Desktop: https://www.docker.com/products/docker-desktop/
- After installation, start Docker Desktop from the Start menu.

> For more details, see the [official Docker documentation](https://docs.docker.com/get-docker/).

---

## 🐳 Docker Shortcuts via setup.py

You can use the `setup.py` script to run common Docker commands with simple flags, instead of typing out long Docker commands:

- **Build the Docker image:**
  ```bash
  python setup.py --docker-build
  sudo python3 setup.py --docker-build
  ```
- **Run the Docker container:**
  ```bash
  python setup.py --docker-run
  sudo python3 setup.py --docker-run
  ```
- **Run the test suite in Docker:**
  ```bash
  python setup.py --docker-test
  sudo python3 setup.py --docker-test
  ```
- **Run a specific test file in Docker:**
  ```bash
  python setup.py --docker-test-file tests/frontend/test_login_ui.py
  sudo python3 setup.py --docker-test-file tests/frontend/test_login_ui.py
  ```
- **Open a shell in the Docker container:**
  ```bash
  python setup.py --docker-shell
  sudo python3 setup.py --docker-shell
  ```

These commands will:
- Use your `.env` file for environment variables
- Mount your local `~/.nypai-chatbot` directory for persistent data
- Expose the application on port 7860

> You can still use the raw Docker commands if you prefer, but the above shortcuts are recommended for convenience.

---

## 🧪 Testing in Docker

The test suite is fully integrated into the Docker container and includes:

### **Frontend Tests**
- Login interface tests
- Chat interface tests  
- Search interface tests
- File upload and audio input tests

### **Backend Tests**
- API endpoint tests
- Database integration tests
- File processing tests

### **Integration Tests**
- End-to-end workflow tests
- Chatbot functionality tests
- File classification tests

### **Running Tests**

**Run all tests:**
```bash
python setup.py --docker-test
```

**Run specific test categories:**
```bash
# Frontend tests only
python setup.py --docker-test-file tests/frontend/run_frontend_tests.py

# Backend tests only  
python setup.py --docker-test-file tests/backend/test_backend.py

# Integration tests only
python setup.py --docker-test-file tests/integration/test_integration.py
```

**Run individual test files:**
```bash
# Login UI tests
python setup.py --docker-test-file tests/frontend/test_login_ui.py

# Chat UI tests
python setup.py --docker-test-file tests/frontend/test_chat_ui.py

# File classification tests
python setup.py --docker-test-file tests/frontend/test_file_classification.py
```

The test suite will:
- Create test Gradio applications to validate UI components
- Test backend API functionality
- Verify file upload and processing capabilities
- Check chat and search functionality
- Validate login and authentication systems

> **Note:** Tests run in a clean Docker environment with all dependencies pre-installed, ensuring consistent test results across different systems.

---

## 🐳 Docker Usage (Recommended)

The application is designed to run seamlessly in Docker with all dependencies (Python 3.12, Tesseract, Pandoc, Poppler, etc.) pre-installed. All Python packages are installed directly from requirements.txt for a clean, reproducible build.

### 1. Prepare your environment variables

Copy the following template to a file named `.env` in the project root:

```
# .env (example)
OPENAI_API_KEY=your_openai_api_key
# Add other required variables as needed
```

Refer to the "Required Environment Variables" section above for all necessary variables.

### 2. Build the Docker image

```bash
docker build -t nyp-fyp-chatbot .
```

### 3. Run the Docker container

```bash
docker run --env-file .env -v /path/on/host/.nypai-chatbot:/root/.nypai-chatbot -p 7860:7860 nyp-fyp-chatbot
```

The application will be available at http://localhost:7860.

---

## 🔥 Firewall Configuration (Linux)

When running the application in Docker on Linux, you may need to configure firewalld to allow external access to the application. The following configurations are only needed if you want to access the app from other machines on your network or from the internet.

### **Local Development (No Firewall Changes Needed)**
If you're only accessing the app from the same machine:
- No firewalld changes required
- Access via `http://localhost:7860`

### **Network Access (Firewall Changes Required)**
If you want to access from other machines on the network:

```bash
# Check if firewalld is running
sudo systemctl status firewalld

# Add port 7860 to the public zone (or your active zone)
sudo firewall-cmd --permanent --add-port=7860/tcp

# Reload firewalld to apply changes
sudo firewall-cmd --reload

# Verify the port is now allowed
sudo firewall-cmd --list-ports
```

### **Alternative: Allow Docker Interface**
For more specific Docker-only access:

```bash
# Get the Docker interface name (usually docker0)
ip addr show docker0

# Add the Docker interface to trusted zone
sudo firewall-cmd --permanent --zone=trusted --add-interface=docker0

# Reload firewalld
sudo firewall-cmd --reload
```

### **Check Your Active Zone**
```bash
# See which zone is active
sudo firewall-cmd --get-active-zones

# If you're using a different zone than 'public', replace 'public' with your zone name
sudo firewall-cmd --permanent --zone=YOUR_ZONE --add-port=7860/tcp
```

### **Testing Firewall Configuration**
```bash
# Test if port 7860 is accessible locally
curl http://localhost:7860

# Test if port 7860 is accessible from network
curl http://YOUR_HOST_IP:7860

# Check if port is listening
netstat -tlnp | grep 7860
# or
ss -tlnp | grep 7860
```

### **Security Considerations**
1. **Only open what you need**: Only add port 7860 if you need external access
2. **Use specific zones**: Consider using a more restrictive zone than 'public'
3. **Monitor access**: Keep an eye on who's accessing your application
4. **Consider VPN**: For production use, consider VPN access instead of direct port exposure

### **Troubleshooting Firewall Issues**
If the app still isn't accessible after adding the firewall rule:

```bash
# Check if Docker is binding to the correct interface
docker ps
docker port <container_id>

# Check if the port is actually listening
sudo netstat -tlnp | grep 7860

# Check firewalld logs
sudo journalctl -u firewalld -f

# Temporarily disable firewalld for testing (remember to re-enable)
sudo systemctl stop firewalld
# Test access
# Then re-enable
sudo systemctl start firewalld
```

---

## 🧪 Running Tests

You can run all or individual test files in Docker using the setup.py CLI flags:

**Run all tests in Docker:**
```bash
python3 setup.py --docker-test
```

Or, for full unittest discovery:

```bash
docker run --env-file .env -v /path/on/host/.nypai-chatbot:/root/.nypai-chatbot -it nyp-fyp-chatbot python -m unittest discover tests
```

### Locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python tests/run_all_tests.py
```

Or:

```bash
python -m unittest discover tests
```

---

## 📁 Project Structure

```
nyp-fyp-project/
├── app.py           # Main application entry point
├── backend.py       # Backend API and business logic
├── utils.py         # Utility functions
├── gradio_modules/  # UI components
│   ├── login_and_register.py # Authentication interface
│   ├── chatbot.py            # Enhanced chatbot interface
│   ├── file_classification.py # File upload & classification
│   ├── audio_input.py        # Audio input interface
│   ├── chat_interface.py     # Legacy (tests only)
│   ├── search_interface.py   # Legacy (tests only)
│   ├── chat_history.py       # Legacy (tests only)
│   └── file_upload.py        # Legacy (tests only)
├── llm/             # Language model services
├── styles/          # CSS and theming
├── scripts/         # JavaScript and client-side code
├── tests/           # Test suite
```

---

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

---

## 🐛 Troubleshooting

### Common Issues

1.  **Import Errors**

      - Ensure you're in the correct directory.
      - Activate the virtual environment.
      - Check that all dependencies are installed.

2.  **API Key Issues**

      - Verify your OpenAI API key is correct.
      - Check that the `.env` file exists and is properly formatted.
      - Ensure the API key has sufficient credits.

3.  **Port Conflicts**

      - The default port is 7860.
      - If occupied, Gradio will automatically use the next available port.

4.  **Environment Variables**

      - Check the `.env` file if using one.
      - Ensure all required variables are set, paying attention to **path separators** (`/` for Linux/macOS, but also accepted by Windows Python).

5.  **Compiler Tools**

      - **Windows**: Microsoft Visual C++ Build Tools are required for ChromaDB functionality. Install the latest MSVC build tools if you encounter compilation errors.
      - **Linux**: Ensure you have `build-essential` (Debian/Ubuntu) or `base-devel` (Arch Linux) installed if you see compilation issues.

6.  **Dependencies**

      - Ensure Pandoc and Tesseract OCR are properly installed and accessible. The `setup.py` script handles this, but if it fails, manual checks might be needed.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

---

## 🖥️ Local Development (Advanced)

If you want to run the application locally (outside Docker):

1. **Create a virtual environment and install dependencies:**

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. **Run the application:**

```bash
python3 app.py
```