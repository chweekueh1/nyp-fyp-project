# syntax=docker/dockerfile:1
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    GRADIO_SERVER_NAME="0.0.0.0" \
    GRADIO_SERVER_PORT="7860" \
    IN_DOCKER="1" \
    PRODUCTION="true" \
    DOCKER_MODE="prod" \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Singapore \
    MAKEFLAGS="-j$(nproc)" \
    PYTHONHASHSEED=random \
    PIP_USE_PEP517=1 \
    PIP_PREFER_BINARY=1 \
    PIP_ONLY_BINARY=:all: \
    NLTK_DATA="/home/appuser/.nypai-chatbot/data/nltk_data"

# Build arguments
ARG PARALLEL_JOBS=4
ARG VENV_PATH=/home/appuser/.nypai-chatbot/venv

# Set environment variables from build args
ENV PIP_JOBS=${PARALLEL_JOBS} \
    VENV_PATH=${VENV_PATH}

WORKDIR /app

# Install system dependencies in a single layer
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    zlib-dev \
    jpeg-dev \
    freetype-dev \
    libpng-dev \
    libgomp \
    libstdc++ \
    libgcc \
    pandoc \
    tesseract-ocr \
    tesseract-ocr-data-eng \
    poppler-utils \
    poppler-dev \
    curl \
    tzdata \
    ca-certificates \
    && update-ca-certificates \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# Create user and directories
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup -s /bin/sh && \
    mkdir -p /home/appuser/.nypai-chatbot/data/{cache,vector_store/chroma_db,memory_persistence,nltk_data,chat_sessions,user_info,uploads,logs} && \
    mkdir -p /app/data && \
    chown -R appuser:appgroup /app && \
    chown -R appuser:appgroup /home/appuser/.nypai-chatbot && \
    chmod -R 755 /home/appuser/.nypai-chatbot && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Create virtual environment
RUN python3 -m venv ${VENV_PATH}
ENV PATH="${VENV_PATH}/bin:$PATH" \
    PYTHONPATH=/app

# Copy requirements first for better layer caching
COPY --chown=appuser:appgroup requirements.txt ./

# Install Python dependencies
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

# Download NLTK data during build time
RUN ${VENV_PATH}/bin/python -c "import nltk; import os; nltk_data_path = '/home/appuser/.nypai-chatbot/data/nltk_data'; os.makedirs(nltk_data_path, exist_ok=True); required_data = ['stopwords', 'punkt', 'wordnet', 'averaged_perceptron_tagger']; [nltk.download(data_name, download_dir=nltk_data_path, quiet=True) for data_name in required_data]; print('NLTK data download completed')"

# Copy application code
COPY --chown=appuser:appgroup app.py performance_utils.py hashing.py flexcyon_theme.py system_prompts.py ./
COPY --chown=appuser:appgroup backend/ ./backend/
COPY --chown=appuser:appgroup gradio_modules/ ./gradio_modules/
COPY --chown=appuser:appgroup llm/ ./llm/
COPY --chown=appuser:appgroup styles/ ./styles/
COPY --chown=appuser:appgroup scripts/entrypoint.py ./
COPY --chown=appuser:appgroup infra_utils/ ./infra_utils/

# Expose port
EXPOSE 7860

# Set entrypoint and command
ENTRYPOINT ["/home/appuser/.nypai-chatbot/venv/bin/python", "/app/entrypoint.py"]
CMD ["python", "app.py"]

# Print build information
RUN echo "[BUILD] Using ENTRYPOINT: ${VENV_PATH}/bin/python /app/entrypoint.py" && \
    echo "[BUILD] Python executable: ${VENV_PATH}/bin/python" && \
    echo "[BUILD] Python version: $(${VENV_PATH}/bin/python --version)" && \
    echo "[BUILD] Pip version: $(${VENV_PATH}/bin/pip --version)" && \
    echo "[BUILD] NLTK data path: ${NLTK_DATA}"
