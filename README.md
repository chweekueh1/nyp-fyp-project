# NYP FYP CNC Chatbot

A chatbot to help staff identify and use correct sensitivity labels in communications.
Built with Python, Gradio, Pandoc, Tesseract OCR, and OpenAI.

## 🚀 Quick Start

Recommended: Use Docker and Docker Compose for setup and running.
> RTFM at <https://www.docker.com/> if not sure

### Prerequisites

- Docker and Docker Compose (v2+)
- OpenAI API key (add to .env)

> See <https://platform.openai.com/api-keys>

- (For local dev: Python 3.11+ and Git)
- Setup & Run (Docker, Docker Compose)

```bash
git clone https://github.com/chweekueh1/nyp-fyp-project
cd nyp-fyp-project
cp .env.dev .env   # Add your OpenAI API key to .env
python setup.py --docker-build
python setup.py --docker-run
```

### 🐳 Docker & Multi-Container

Uses separate containers for dev, test, prod, and docs.
Requires Docker Compose for multi-container workflows and benchmarks.
See Docker Compose install.

Common commands:

```bash
python setup.py --docker-build         # Build dev container
python setup.py --docker-run           # Run app
python setup.py --docker-test          # Run tests
python setup.py --docs                 # Build & serve docs (http://localhost:8080)
```

### 🧪 Testing

To be implemented

### 📁 Data Storage

User data is stored in ~/.nypai-chatbot/ (local) or /home/appuser/.nypai-chatbot/ (Docker).
Test and production user data are separated.

### 📚 Documentation

Build and serve docs:

```bash
python setup.py --docs
```

Docs available at <http://127.0.0.1:8080>

### 🔧 Code Quality

Pre-commit hooks with ruff for linting and formatting:

```bash
python setup.py --pre-commit
```

### 🐛 Troubleshooting

API Key Issues: Check .env and your OpenAI API key.
Port Conflicts: Default is 7860; Gradio will use the next available port.
Compiler Tools: On Windows, install MSVC Build Tools for ChromaDB.
Dependencies: Pandoc and Tesseract OCR are required (handled by Docker).

### 📝 License

MIT License. See [LICENSE](./LICENSE) for details.
