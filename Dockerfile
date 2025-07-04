# syntax=docker/dockerfile:1

# Single-stage Dockerfile for NYP FYP Chatbot
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"
ENV IN_DOCKER="1"
ENV PRODUCTION="true"
ENV DOCKER_MODE="prod"
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV TZ=Asia/Singapore

# Set build optimization environment variables
ENV MAKEFLAGS="-j$(nproc)"
ENV PYTHONHASHSEED=random
ENV PIP_USE_PEP517=1

# Add pip parallelization and optimization
ARG PARALLEL_JOBS=4
ENV PIP_JOBS=${PARALLEL_JOBS}
ENV PIP_PREFER_BINARY=1
ENV PIP_ONLY_BINARY=:all:

# Add venv path argument (default for prod)
ARG VENV_PATH=/home/appuser/.nypai-chatbot/venv
ENV VENV_PATH=${VENV_PATH}

WORKDIR /app

# Install system dependencies (including document processing) with parallel optimization
RUN apk add --no-cache \
    # Core build dependencies for Python packages
    build-base \
    libffi-dev \
    openssl-dev \
    zlib-dev \
    # Image processing dependencies (for Pillow)
    jpeg-dev \
    freetype-dev \
    libpng-dev \
    # Core runtime dependencies
    libgomp \
    libstdc++ \
    libgcc \
    # Document processing dependencies
    pandoc \
    tesseract-ocr \
    tesseract-ocr-data-eng \
    poppler-utils \
    poppler-dev \
    curl \
    # Timezone support
    tzdata \
    # Security and performance
    ca-certificates \
    && update-ca-certificates \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create necessary directories and set up user in a single layer
RUN mkdir -p data && \
    addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup -s /bin/sh && \
    mkdir -p /home/appuser/.nypai-chatbot/data && \
    mkdir -p /home/appuser/.nypai-chatbot/uploads && \
    mkdir -p /home/appuser/.nypai-chatbot/test_uploads && \
    chown -R appuser:appgroup /app && \
    chown -R appuser:appgroup /home/appuser/.nypai-chatbot && \
    chmod -R 755 /home/appuser/.nypai-chatbot && \
    chmod -R 755 /app


COPY scripts/entrypoint.py /usr/local/bin/entrypoint.py

USER appuser

# Ensure venv is created inside the container, not copied from host
RUN python3 -m venv ${VENV_PATH}

# Copy requirements and install Python dependencies with advanced parallelization
COPY requirements.txt ./requirements.txt

# Install uv and use it for fast parallel package installation
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    chmod +x $HOME/.local/bin/uv && \
    export PATH="$HOME/.local/bin:$PATH" && \
    ${VENV_PATH}/bin/pip install --upgrade pip wheel setuptools && \
    ${VENV_PATH}/bin/pip install uv && \
    export VIRTUAL_ENV=${VENV_PATH} && \
    uv pip install --upgrade pip wheel setuptools && \
    uv pip install --prerelease=allow -r requirements.txt && \
    uv pip install --prerelease=allow overrides tenacity rich tqdm typer && \
    ${VENV_PATH}/bin/python -c "import yake; print('YAKE import OK')" && \
    uv pip install --prerelease=allow --no-deps unstructured

# Copy all application files in a single layer to reduce layers and improve caching
COPY app.py backend.py infra_utils.py performance_utils.py hashing.py flexcyon_theme.py ./
COPY backend/ ./backend/
COPY gradio_modules/ ./gradio_modules/
COPY llm/ ./llm/
COPY styles/ ./styles/
COPY scripts/ ./scripts/
# Note: .env file should be passed at runtime via --env-file
# Tests are not needed in production image

# Set PYTHONPATH so all modules are importable
ENV PYTHONPATH=/app

# Dependencies already installed via uv above

# Expose the port Gradio will listen on
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ${VENV_PATH}/bin/python -c "import requests; requests.get('http://localhost:7860/')" || exit 1

# Set the entrypoint and default command
RUN echo "[BUILD] Using ENTRYPOINT: ${VENV_PATH}/bin/python /usr/local/bin/entrypoint.py"
ENTRYPOINT ["sh", "-c", "${VENV_PATH}/bin/python /usr/local/bin/entrypoint.py \"$@\"", "--"]
CMD ["sh", "-c", "${VENV_PATH}/bin/python app.py"]

# Set the shell so that the venv is always activated for RUN commands
SHELL ["/bin/sh", "-c"]
ENV PATH="${VENV_PATH}/bin:$PATH"

RUN echo "[BUILD] VENV_PATH is $VENV_PATH"
