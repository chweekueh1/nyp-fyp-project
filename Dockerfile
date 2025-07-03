# syntax=docker/dockerfile:1

# Single-stage Dockerfile for NYP FYP Chatbot
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"
ENV IN_DOCKER="1"
ENV PRODUCTION="true"
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Set build optimization environment variables
ENV MAKEFLAGS="-j$(nproc)"
ENV PYTHONHASHSEED=random
ENV PIP_USE_PEP517=1

# Add pip parallelization and optimization
ARG PARALLEL_JOBS=4
ENV PIP_JOBS=${PARALLEL_JOBS}
ENV PIP_PREFER_BINARY=1
ENV PIP_ONLY_BINARY=:all:

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
    # Security and performance
    ca-certificates \
    && update-ca-certificates

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies with advanced parallelization
COPY requirements.txt ./requirements.txt

# Use build cache mount for pip cache and optimize pip installation with parallelization
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip wheel setuptools && \
    pip install --no-cache-dir --use-pep517 --parallel ${PARALLEL_JOBS} --prefer-binary -r requirements.txt && \
    pip install --no-cache-dir --use-pep517 --parallel ${PARALLEL_JOBS} --prefer-binary overrides tenacity rich tqdm typer

# Copy all application files in a single layer to reduce layers and improve caching
COPY app.py backend.py infra_utils.py performance_utils.py hashing.py flexcyon_theme.py ./
COPY backend/ ./backend/
COPY gradio_modules/ ./gradio_modules/
COPY llm/ ./llm/
COPY styles/ ./styles/
COPY scripts/ ./scripts/

# Create necessary directories and set up user in a single layer
RUN mkdir -p logs data && \
    addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose the port Gradio will listen on
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7860/')" || exit 1

# Set the default command to run the main application
CMD ["python", "app.py"]
