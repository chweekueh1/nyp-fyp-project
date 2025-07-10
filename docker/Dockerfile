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
    PIP_ONLY_BINARY=:all:

# Build arguments
ARG PARALLEL_JOBS=4
ARG VENV_PATH=/home/appuser/.nypai-chatbot/venv-prod

# Set environment variables from build args
ENV PIP_JOBS=${PARALLEL_JOBS} \
    VENV_PATH=${VENV_PATH}

WORKDIR /app

# Install system dependencies in a single layer - Alpine Linux friendly
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
    poppler-utils \
    tesseract-ocr \
    curl \
    tzdata \
    ca-certificates \
    git \
    hyperfine \
    imagemagick \
    vim \
    nano \
    netcat-openbsd \
    gzip \
    bzip2 \
    xz \
    procps \
    sysstat \
    wkhtmltopdf \
    && update-ca-certificates \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# Create user and directories
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup -s /bin/sh && \
    mkdir -p /home/appuser/.nypai-chatbot/data/{cache,vector_store/chroma_db,memory_persistence,nltk_data,chat_sessions,user_info,uploads,test_uploads,logs} && \
    mkdir -p /app/data && \
    mkdir -p /app/docs/modules /app/docs/modules/src && \
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

# Copy requirements first for better caching
COPY --chown=appuser:appgroup requirements/requirements.txt .

# Install Python dependencies
RUN ${VENV_PATH}/bin/pip install --upgrade pip wheel setuptools && \
    ${VENV_PATH}/bin/pip install -r requirements.txt

# Copy application code
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup styles/ ./styles/
COPY --chown=appuser:appgroup src/scripts/entrypoint.py ./
COPY --chown=appuser:appgroup src/tests/ ./tests/

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Set entrypoint and command
ENTRYPOINT ["/home/appuser/.nypai-chatbot/venv-prod/bin/python", "/app/entrypoint.py"]
CMD ["python", "src/app.py"]

# Print build information
RUN echo "[BUILD] Using ENTRYPOINT: ${VENV_PATH}/bin/python /app/entrypoint.py" && \
    echo "[BUILD] Python executable: ${VENV_PATH}/bin/python" && \
    echo "[BUILD] Python version: $(${VENV_PATH}/bin/python --version)" && \
    echo "[BUILD] Pip version: $(${VENV_PATH}/bin/pip --version)"
