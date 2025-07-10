"""
NYP FYP CNC Chatbot Project README

This file provides an overview, installation instructions, and usage details for the NYP FYP CNC Chatbot project. It is not a Python module, but if included in Sphinx autodoc, this docstring will be used.
"""

# NYP FYP CNC Chatbot

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

6. **Run with Docker (Recommended)**

    ```bash
    python setup.py --docker-build
    python setup.py --docker-run
    ```

7. **Access the application**

    Open <http://localhost:7860> in your browser

## 📋 TODO

* [ ] Integrate scripts.js to trigger search in each relevant tab
* [ ] Push Docker image at the end of FYP

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

6. **Run with Docker (Recommended)**

    ```bash
    python setup.py --docker-build
    python setup.py --docker-run
    ```

7. **Access the application**

    Open <http://localhost:7860> in your browser

## 🐳 Docker Multi-Container Architecture

The project uses separate Docker containers for different purposes. For detailed information about the multi-container setup, testing procedures, and container-specific features, see the [Tests README](tests/README.md#docker-container-architecture).

### Quick Commands

```bash
# Build containers (Python 3.11 Alpine)
python setup.py --docker-build        # Development
python setup.py --docker-build-test   # Testing
python setup.py --docker-build-prod   # Production
python setup.py --docs                # Documentation

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
* **Docker**: `/home/appuser/.nypai-chatbot/` (mounted from host `~/.nypai-chatbot/`)

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

## 🐳 Docker Usage (Cross-Platform)

The application is designed to run seamlessly in Docker with all dependencies (Python 3.11, Tesseract, Pandoc, Poppler, etc.) pre-installed. All Python packages are installed directly from requirements.txt for a clean, reproducible build.

### **Cross-Platform Support**

✅ **Linux**: Full support with automatic Docker daemon management
✅ **macOS**: Full support via Docker Desktop
✅ **Windows**: Full support via Docker Desktop with automatic path conversion

### Quick Start

```bash
# Build and run the development container
python setup.py --docker-build
python setup.py --docker-run
```

The application will be available at <http://localhost:7860>.

### **Windows-Specific Notes**

* **Docker Desktop**: Must be installed and running
* **Path Conversion**: Automatic conversion of Windows paths to Docker format
* **Permissions**: Uses Windows `icacls` for permission management
* **Volume Mounts**: Automatically converts `C:\Users\...` to `/c/Users/...`

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
   # Linux/macOS
   docker run --env-file .env -v ~/.nypai-chatbot:/home/appuser/.nypai-chatbot -p 7860:7860 nyp-fyp-chatbot

   # Windows (PowerShell)
   docker run --env-file .env -v ${env:USERPROFILE}\.nypai-chatbot:/home/appuser/.nypai-chatbot -p 7860:7860 nyp-fyp-chatbot
   ```

---

## 📚 Documentation Generation

The project includes comprehensive Sphinx documentation generation that automatically documents all Python modules, functions, and classes. The documentation is built using Docker and served via HTTP.
> Not everything is documented as there are constant changes to certain APIs

### **Quick Start - Generate Documentation**

```bash
# Generate and serve documentation
python setup.py --docs
```

This will:

1. Build a Docker container with all documentation dependencies
2. Generate comprehensive API documentation for all modules
3. Start an HTTP server on port 8080
4. Make documentation available at <http://localhost:8080>

### **Documentation Features**

✅ **Complete API Coverage**: Documents all Python modules, functions, and classes
✅ **Automatic Module Discovery**: Recursively finds and documents all code files
✅ **Cross-Reference Support**: Links between related functions and modules
✅ **Search Functionality**: Full-text search across all documentation
✅ **Modern Theme**: Uses Piccolo theme for clean, responsive design
✅ **Docker-Based**: Consistent build environment across platforms

### **What Gets Documented**

The documentation generator covers:

* **Backend Modules**: All backend functionality (`backend/`, `auth.py`, `chat.py`, etc.)
* **Gradio Interface**: All UI components (`gradio_modules/`)
* **LLM Components**: AI/ML functionality (`llm/`)
* **Infrastructure**: Utilities and configuration (`infra_utils/`, `scripts/`)
* **Test Suite**: All test files and utilities (`tests/`)
* **Root Modules**: Main application files (`app.py`, `setup.py`, etc.)

### **Documentation Structure**

```
Documentation
├── Backend Modules          # Core backend functionality
├── Gradio Modules          # UI components and interfaces
├── LLM Modules            # AI/ML and language model components
├── Infrastructure Modules  # Utilities, scripts, and configuration
├── Tests                  # Complete test suite documentation
└── Root Modules           # Main application entry points
```

### **Troubleshooting Documentation Build**

#### **UV Installation Failures**

The documentation build uses `uv` for fast dependency installation. Occasionally, `uv` may fail due to network connectivity issues:

```
error: Failed to fetch: `https://pypi.org/simple/pypdfium2/`
Caused by: peer closed connection without sending TLS close_notify
```

**Solution**: Simply try again - this is usually a temporary network issue:

```bash
# Clean up and retry
python setup.py --docker-wipe
python setup.py --docs
```

**Why this happens**: `uv` uses Rust-based networking which can be sensitive to TLS handshake issues in some Docker environments. The failure is temporary and retrying usually resolves it.

#### **Other Common Issues**

1. **Port 8080 Already in Use**

   ```bash
   # Check what's using the port
   lsof -i :8080
   # Or use a different port by modifying scripts/serve_docs.sh
   ```

2. **Docker Build Fails**

   ```bash
   # Clean up Docker and retry
   python setup.py --docker-wipe
   python setup.py --docs
   ```

3. **Documentation Not Updating**

   ```bash
   # Force rebuild by wiping Docker cache
   python setup.py --docker-wipe
   python setup.py --docs
   ```

### **Advanced Documentation Options**

#### **Manual Docker Commands**

If you prefer to build documentation manually:

```bash
# Build documentation container
docker build --progress=plain -f Dockerfile.docs -t nyp-fyp-chatbot:docs .

# Run documentation server
docker run --name nyp-fyp-chatbot-docs -p 8080:8080 nyp-fyp-chatbot:docs
```

#### **Local Documentation Development**

For documentation development without Docker:

```bash
# Install documentation dependencies
pip install -r requirements-docs.txt

# Generate documentation locally
cd docs
sphinx-apidoc -o modules --separate --module-first --maxdepth=6 --private --no-headings ../backend ../gradio_modules ../llm ../infra_utils ../scripts ../tests ../misc ../
sphinx-build -b html . _build/html

# Serve locally
python -m http.server 8080 --directory _build/html
```

### **Documentation Configuration**

The documentation is configured in:

* `docs/conf.py`: Sphinx configuration
* `scripts/generate_docs.py`: Documentation generation script
* `scripts/serve_docs.sh`: Documentation server script
* `requirements-docs.txt`: Documentation-specific dependencies

### **Customizing Documentation**

To customize the documentation:

1. **Add new modules**: They'll be automatically discovered and documented
2. **Modify theme**: Edit `docs/conf.py` to change the Sphinx theme
3. **Add custom pages**: Create `.rst` files in the `docs/` directory
4. **Update structure**: Modify `scripts/generate_docs.py` to change organization

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
├── app.py                          # Main Gradio application entry point
├── backend.py                      # Legacy backend (being modularized)
├── infra_utils.py                  # Infrastructure utilities (logging, paths)
├── performance_utils.py            # Performance optimization utilities
├── hashing.py                      # Password hashing utilities
├── flexcyon_theme.py               # Custom Gradio theme
├── setup.py                        # Build, test, and deployment automation
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Production Docker image
├── Dockerfile.dev                  # Development Docker image
├── Dockerfile.test                 # Test Docker image
├── Dockerfile.docs                 # Documentation Docker image
├── .env.dev                        # Environment variables template
├── .pre-commit-config.yaml         # Pre-commit hooks configuration
├── ruff.toml                       # Ruff linter configuration
│
├── backend/                        # Modular backend components
│   ├── __init__.py
│   ├── main.py                     # Main backend entry point
│   ├── auth.py                     # Authentication and user management
│   ├── chat.py                     # Chat functionality
│   ├── database.py                 # Database operations
│   ├── file_handling.py            # File upload and processing
│   ├── audio.py                    # Audio processing
│   ├── config.py                   # Configuration management
│   ├── rate_limiting.py            # Rate limiting utilities
│   └── utils.py                    # Backend utilities
│
├── gradio_modules/                 # Gradio UI components
│   ├── chat_interface.py           # Main chat interface
│   ├── file_upload.py              # File upload component
│   ├── file_classification.py      # File classification UI
│   ├── audio_input.py              # Audio input component
│   ├── chat_history.py             # Chat history display
│   ├── search_interface.py         # Search functionality
│   ├── login_and_register.py       # Authentication UI
│   ├── change_password.py          # Password change UI
│   ├── chatbot.py                  # Core chatbot component
│   ├── enhanced_content_extraction.py  # Content extraction
│   └── classification_formatter.py # Classification formatting
│
├── llm/                           # LLM and AI components
│   ├── chatModel.py               # Chat model implementation
│   ├── classificationModel.py     # Classification model
│   ├── dataProcessing.py          # Data processing utilities
│   └── keyword_cache.py           # Keyword caching system
│
├── scripts/                       # Utility scripts
│   ├── scripts.js                 # JavaScript utilities
│   ├── entrypoint.sh              # Docker entrypoint script
│   ├── generate_docs.py           # Documentation generation script
│   └── serve_docs.sh              # Documentation server script
│
├── styles/                        # CSS styling
│   ├── styles.css                 # Main stylesheet
│   └── performance.css            # Performance optimizations
│
├── docs/                          # Documentation
│   ├── conf.py                    # Sphinx configuration
│   ├── index.rst                  # Documentation index
│   └── Makefile                   # Documentation build rules
│
├── requirements-docs.txt          # Documentation dependencies
│
├── tests/                         # Comprehensive test suite
│   ├── README.md                  # Test documentation
│   ├── run_all_tests.py           # Test runner
│   ├── run_tests.py               # Alternative test runner
│   ├── comprehensive_test_suite.py # Main test orchestrator
│   ├── test_utils.py              # Test utilities
│   ├── test_data_storage.py       # Data storage tests
│   ├── test_docker_environment.py # Docker environment tests
│   │
│   ├── backend/                   # Backend tests
│   │   ├── test_backend.py        # Core backend tests
│   │   ├── test_backend_fixes_and_rename.py
│   │   ├── test_modular_backend.py # Modular backend tests
│   │   └── test_special_characters.py
│   │
│   ├── frontend/                  # Frontend tests
│   │   ├── test_all_interfaces.py # All UI components
│   │   ├── test_chat_ui.py        # Chat interface tests
│   │   ├── test_file_upload_ui.py # File upload tests
│   │   ├── test_login_ui.py       # Login interface tests
│   │   ├── test_chatbot_ui.py     # Chatbot component tests
│   │   ├── test_search_ui.py      # Search interface tests
│   │   ├── test_search_ui.py # Search interface tests
│   │   ├── test_file_audio_ui.py  # Audio interface tests
│   │   ├── test_file_classification.py # Classification tests
│   │   ├── test_change_password_functionality.py
│   │   ├── test_ui_fixes.py       # UI fixes and improvements
│   │   ├── test_theme_styles.py   # Theme and styling tests
│   │   └── test_ui_state_interactions.py
│   │
│   ├── integration/               # Integration tests
│   │   ├── test_integration.py    # Core integration tests
│   │   ├── test_chatbot_integration.py
│   │   ├── test_enhanced_chatbot_features.py
│   │   ├── test_file_classification_integration.py
│   │   └── test_improved_app.py
│   │
│   ├── performance/               # Performance tests
│   │   ├── test_optimized_performance.py
│   │   ├── test_startup_tracking.py
│   │   ├── test_comprehensive_test_suite_fixes.py
│   │   ├── test_demo_organization.py
│   │   ├── test_final_organization_verification.py
│   │   ├── test_logging_and_dependency_paths.py
│   │   ├── test_syntax_and_formatting_fixes.py
│   │   ├── test_enhanced_classification_core.py
│   │   ├── test_enhanced_file_classification.py
│   │   ├── test_file_path_and_logout_fixes.py
│   │   ├── test_file_path_isolation.py
│   │   ├── test_file_upload_backend_fix.py
│   │   ├── test_file_upload_location_fix.py
│   │   ├── test_complete_login_features.py
│   │   ├── test_chat_button_styling.py
│   │   └── test_dynamic_login_interface.py
│   │
│   ├── llm/                       # LLM-specific tests
│   │   └── test_llm.py
│   │
│   ├── demos/                     # Demo applications
│   │   ├── README.md
│   │   ├── demo_audio_interface.py
│   │   ├── demo_chatbot_with_history.py
│   │   ├── demo_data_storage.py
│   │   ├── demo_enhanced_chatbot.py
│   │   ├── demo_enhanced_classification.py
│   │   ├── demo_file_classification.py
│   │   └── demo_final_working_chatbot.py
│   │
│   └── utils/                     # Test utilities
│       ├── debug_chatbot_ui.py
│       ├── diagnose_chatbot_issue.py
│       └── minimal_chatbot_test.py
│
└── misc/                          # Documentation and notes
    ├── BUILD_OPTIMIZATION.md      # Build optimization notes
    ├── DEPENDENCY_FIXES.md        # Dependency resolution notes
    ├── DEPENDENCY_INSTALLATION.md # Installation troubleshooting
    ├── FILE_CLASSIFICATION_IMPLEMENTATION.md
    ├── ORGANIZATION_SUMMARY.md    # Project organization notes
    ├── TODO.md                    # Development tasks
    └── verify_chatbot_integration.md
```

### **Key Features**

* **Modular Architecture**: Backend components are organized into focused modules
* **Comprehensive Testing**: Extensive test suite covering unit, integration, and performance tests
* **Docker Support**: Multiple Docker configurations for development, testing, and production
* **UI Components**: Reusable Gradio components for different functionalities
* **LLM Integration**: Dedicated modules for AI/ML functionality
* **Performance Optimization**: Utilities for monitoring and improving performance
* **Auto-Generated Documentation**: Comprehensive Sphinx documentation for all code modules

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

## 📚 Additional Documentation

For detailed technical information, see the `misc/` directory:

* **`misc/DOCUMENTATION_GENERATION.md`**: Comprehensive documentation generation system guide
* **`misc/DOCKER_BUILD_OPTIMIZATION.md`**: Docker build optimization details and size comparisons
* **`misc/DEPENDENCY_FIXES.md`**: Dependency resolution and fixes applied
* **`misc/FILE_CLASSIFICATION_IMPLEMENTATION.md`**: Detailed file classification feature implementation
* **`misc/verify_chatbot_integration.md`**: Chatbot integration verification details

## 📋 TODO

## 🐍 Deterministic Python Virtual Environment

All development and testing should use the deterministic virtual environment at `~/.nypai-chatbot/venv`.

### Setup (first time only)

```sh
python3 -m venv ~/.nypai-chatbot/venv
~/.nypai-chatbot/venv/bin/pip install --upgrade pip
~/.nypai-chatbot/venv/bin/pip install -r requirements.txt
```

### To activate the venv for your shell

```sh
source scripts/activate_nypai_venv.sh
```

All Python commands (including running setup.py, tests, etc.) should be run with this venv activated.
