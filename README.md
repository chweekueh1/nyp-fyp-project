# NYP FYP CNC Chatbot

A Gradio-based Python chatbot application designed to help staff identify and use the correct sensitivity labels in their communications. The application features login, registration, chat, and search functionalities.

---

## About

The NYP-FYP CNC Chatbot is a chatbot used to help staff identify and use the correct sensitivity labels in their communications. It makes use of the Python programming language, along with integrations of Gradio, Pandoc, Tesseract OCR and OpenAI.

---

> **Recommended:** Use Docker for the easiest and most reliable setup. See the Docker Usage section below. The `setup.py` script is only needed for advanced local development outside Docker.

## 🚀 Quick Start

### Prerequisites

* **Python 3.11.0 or higher**: Ensure you have a compatible Python version installed.
* **Git**: Required for cloning the repository.
* **OpenAI API key**: Necessary for AI functionalities.

### Installation

1. **Clone the repository**

    ```bash
    git clone <repository-url>
    cd nyp-fyp-project
    ```

2. **Install Python Version 3.11.0 (if you don't have it)**

      * **Windows**: You can download it from [Python.org](https://www.python.org/downloads/release/python-3119/). During installation, make sure to **check the box "Add python.exe to PATH"**.
      * **Linux**: It's recommended to install Python via your distribution's package manager (e.g., `sudo apt install python3.11` on Debian/Ubuntu, `sudo pacman -S python` on Arch Linux) or using a version manager like `pyenv`.

3. **The rest of the installation is handled by the setup script. Proceed to step 7!**
    (The setup script will create and manage the virtual environment, install Python dependencies, and set up Pandoc/Tesseract.)

4. **Set up environment variables**

    ```bash
    # Copy the development environment template
    cp .env.dev .env

    # Edit .env and add your OpenAI API key
    # OPENAI_API_KEY=your_openai_api_key
    ```

5. **Run the setup script**

    ```bash
    python setup.py
    ```

    The Docker image will take a while to build for the first time (2 to 3 minutes) as it sets up all required dependencies, including creating a virtual environment, installing Python packages, and configuring Pandoc and Tesseract OCR.

---

## 🐳 Docker Multi-Container Architecture

The project uses separate Docker containers for different purposes. For detailed information about the multi-container setup, testing procedures, and container-specific features, see the [Tests README](tests/README.md#docker-container-architecture).

### Quick Commands

```bash
# Build containers (Python 3.11 Alpine)
python setup.py --docker-build        # Development
python setup.py --docker-build-test   # Testing
python setup.py --docker-build-prod   # Production

# Run application
python setup.py --docker-run

# Run tests (see tests/README.md for detailed options)
python setup.py --list-tests                                     # List all available tests
python setup.py --docker-test                                    # Environment verification
python setup.py --docker-test-suite frontend                     # Frontend test suite
python setup.py --docker-test-suite backend                      # Backend test suite
python setup.py --docker-test-suite integration                  # Integration test suite
python setup.py --docker-test-suite performance                  # Performance test suite
python setup.py --docker-test-suite comprehensive                # Comprehensive test suite
python setup.py --docker-test-suite all                          # All test suites
python setup.py --docker-test-file tests/backend/test_backend_fixes_and_rename.py
```

---

## 🐳 Installing Docker

Docker is required to build and run the application in a containerized environment. Follow the instructions for your platform:

### Linux

* **Recommended:** Use your distribution's package manager or the official Docker installation script.
* Official instructions: <https://docs.docker.com/engine/install/>
* Example for Ubuntu:

  ```bash
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl gnupg
  sudo install -m 0755 -d /etc/apt/keyringos
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

* Download and install Docker Desktop: <https://www.docker.com/products/docker-desktop/>
* After installation, start Docker Desktop from Applications.

### Windows

* Download and install Docker Desktop: <https://www.docker.com/products/docker-desktop/>
* After installation, start Docker Desktop from the Start menu.

> For more details, see the [official Docker documentation](https://docs.docker.com/get-docker/).

---

## 📁 Data Storage

The application stores user data in a dedicated directory to ensure data persistence and separation between production and test environments.

### **Data Location**

* **Local Development**: `~/.nypai-chatbot/`
* **Docker**: `/root/.nypai-chatbot/` (mounted from host `~/.nypai-chatbot/`)

### **Directory Structure**

```
~/.nypai-chatbot/
├── data/
│   ├── chat_sessions/     # User chat history
│   ├── user_info/
│   │   ├── users.json     # Production user accounts
│   │   └── test_users.json # Test user accounts (separate)
│   └── vector_store/
│       └── chroma_db/     # Vector database for embeddings
└── logs/                  # Application logs
```

### **Data Protection**

* ✅ **User data is preserved** during builds and updates
* ✅ **Test users are isolated** from production users
* ✅ **Chat sessions persist** across application restarts
* ✅ **Build system won't override** existing user data

### **User Database Separation**

* **Production Users**: Stored in `users.json`
* **Test Users**: Stored in `test_users.json` (completely separate)

This ensures that:

* Test runs don't affect production user data
* Production users are never accidentally deleted during testing
* Test data can be easily cleaned up without affecting real users

### **Viewing Data Storage Info**

```bash
# Show data storage configuration
python demo_data_storage.py

# Run data storage tests
python tests/test_data_storage.py
```

---

## 🧪 Testing

For comprehensive testing information, including Docker test containers, test categories, and detailed testing procedures, see the [Tests README](tests/README.md).

### Quick Test Commands

```bash
# List all available tests and suites
python setup.py --list-tests

# Run environment verification
python setup.py --docker-test

# Run specific test suites
python setup.py --docker-test-suite frontend      # Frontend UI tests
python setup.py --docker-test-suite backend       # Backend API tests
python setup.py --docker-test-suite integration   # Integration tests
python setup.py --docker-test-suite performance   # Performance tests
python setup.py --docker-test-suite comprehensive # All tests organized by category
python setup.py --docker-test-suite all           # Run all available tests

# Run individual test files
python setup.py --docker-test-file tests/backend/test_backend_fixes_and_rename.py
```

## 🔧 Code Quality with Pre-commit

The project includes pre-commit hooks for automatic code quality checks and formatting using [ruff](https://github.com/astral-sh/ruff).

### **Setup Pre-commit Hooks**

```bash
# Install pre-commit hooks with ruff
python setup.py --pre-commit
```

This will:

* Install pre-commit in your virtual environment
* Install git hooks for automatic code quality checks
* Run ruff on all files to fix formatting issues

### **What Pre-commit Does**

The pre-commit hooks automatically:

* **Format code** using ruff-format
* **Lint code** using ruff with auto-fix
* **Check for common issues** like unused imports, undefined variables, etc.

### **Usage**

**Automatic (on git commit):**

```bash
git add .
git commit -m "Your commit message"
# Pre-commit hooks run automatically
```

**Manual runs:**

```bash
# Run on all files
pre-commit run --all-files

# Run on specific files
pre-commit run --files file1.py file2.py

# Run specific hooks
pre-commit run ruff --all-files
pre-commit run ruff-format --all-files
```

### **Configuration**

The `.pre-commit-config.yaml` file includes:

* **ruff**: Fast Python linter with auto-fix
* **ruff-format**: Fast Python code formatter

### **Testing Pre-commit Setup**

```bash
# Test that pre-commit is properly configured
python tests/test_pre_commit_setup.py
```

### **Troubleshooting**

If pre-commit hooks fail:

1. **Auto-fix issues**: `pre-commit run --all-files`
2. **Skip hooks temporarily**: `git commit --no-verify`
3. **Update hooks**: `pre-commit autoupdate`

---

## 🐳 Docker Usage (Recommended)

The application is designed to run seamlessly in Docker with all dependencies (Python 3.11, Tesseract, Pandoc, Poppler, etc.) pre-installed. All Python packages are installed directly from requirements.txt for a clean, reproducible build.

### Quick Start

```bash
# Build and run the development container
python setup.py --docker-build
python setup.py --docker-run
```

The application will be available at <http://localhost:7860>.

### Manual Docker Commands (Advanced)

If you prefer to use Docker commands directly:

1. **Prepare your environment variables**

   ```bash
   # Copy the template
   cp .env.dev .env
   # Edit .env and add your OpenAI API key
   ```

2. **Build the Docker image**

   ```bash
   docker build -t nyp-fyp-chatbot .
   ```

3. **Run the Docker container**

   ```bash
   docker run --env-file .env -v ~/.nypai-chatbot:/root/.nypai-chatbot -p 7860:7860 nyp-fyp-chatbot
   ```

---

## 🔥 Firewall Configuration (Linux)

When running the application in Docker on Linux, you may need to configure firewalld to allow external access to the application. The following configurations are only needed if you want to access the app from other machines on your network or from the internet.

### **Local Development (No Firewall Changes Needed)**

If you're only accessing the app from the same machine:

* No firewalld changes required
* Access via `http://localhost:7860`

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

## 📁 Project Structure

```
nyp-fyp-project/
├── app.py                    # Main application entry point
├── backend.py                # Backend API and business logic
├── setup.py                  # Build and deployment scripts
├── requirements.txt          # Python dependencies
├── Dockerfile*               # Multi-container Docker setup
├── gradio_modules/           # UI components
│   ├── login_and_register.py # Authentication interface
│   ├── chatbot.py            # Enhanced chatbot interface
│   ├── file_classification.py # File upload & classification
│   ├── audio_input.py        # Audio input interface
│   ├── chat_interface.py     # Legacy (tests only)
│   ├── search_interface.py   # Legacy (tests only)
│   ├── chat_history.py       # Legacy (tests only)
│   └── file_upload.py        # Legacy (tests only)
├── llm/                      # Language model services
│   ├── chatModel.py          # Chat functionality
│   ├── classificationModel.py # Document classification
│   └── dataProcessing.py     # Data processing utilities
├── styles/                   # CSS and theming
├── scripts/                  # JavaScript and client-side code
├── tests/                    # Comprehensive test suite
│   ├── frontend/             # UI component tests
│   ├── backend/              # Backend functionality tests
│   ├── integration/          # End-to-end tests
│   ├── llm/                  # Language model tests
│   ├── demos/                # Interactive demonstrations
│   └── utils/                # Testing utilities
└── misc/                     # Documentation and utilities
```

For detailed test structure, see [tests/README.md](tests/README.md#directory-structure).

---

## 📊 Features

* **Sensitivity Label Assistance**: Help staff identify and use correct sensitivity labels
* **User Authentication**: Login and registration system
* **Chat Interface**: Real-time chat with AI assistant
* **Search Functionality**: Search through chat history
* **File Upload**: Support for document upload and processing (PDF, DOCX, etc.)
* **Audio Input**: Voice-to-text functionality
* **Chat History**: Persistent chat sessions
* **Global Search**: Command-based navigation and search
* **OCR Integration**: Text extraction from images using Tesseract
* **Document Processing**: Support for various document formats via Pandoc

---

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**

      * Ensure you're in the correct directory.
      * Activate the virtual environment.
      * Check that all dependencies are installed.

2. **API Key Issues**

      * Verify your OpenAI API key is correct.
      * Check that the `.env` file exists and is properly formatted.
      * Ensure the API key has sufficient credits.

3. **Port Conflicts**

      * The default port is 7860.
      * If occupied, Gradio will automatically use the next available port.

4. **Environment Variables**

      * Check the `.env` file if using one.
      * Ensure all required variables are set, paying attention to **path separators** (`/` for Linux/macOS, but also accepted by Windows Python).

5. **Compiler Tools**

      * **Windows**: Microsoft Visual C++ Build Tools are required for ChromaDB functionality. Install the latest MSVC build tools if you encounter compilation errors.
      * **Linux**: Ensure you have `build-essential` (Debian/Ubuntu) or `base-devel` (Arch Linux) installed if you see compilation issues.

6. **Dependencies**

      * Ensure Pandoc and Tesseract OCR are properly installed and accessible. The `setup.py` script handles this, but if it fails, manual checks might be needed.

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
