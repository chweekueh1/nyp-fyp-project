# syntax=docker/dockerfile:1

# Multi-stage build: Use Python slim for dependency installation
FROM python:3.12-slim AS builder

# Install system dependencies for building Python packages
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        libffi-dev \
        libssl-dev \
        zlib1g-dev \
        libjpeg-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libopenjp2-7-dev \
        libtiff5-dev \
        tk-dev \
        tcl-dev \
        libharfbuzz-dev \
        libfribidi-dev \
        libimagequant-dev \
        libxcb1-dev \
        libpng-dev \
        cmake \
        ninja-build \
        pkg-config \
        && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Final stage: Use Alpine for runtime
FROM python:3.12-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"

WORKDIR /app

# Install runtime system dependencies (Alpine packages)
RUN apk add --no-cache \
    tesseract-ocr \
    pandoc-cli \
    poppler-utils \
    unzip \
    curl \
    git \
    # Runtime libraries needed for Python packages
    libffi \
    openssl \
    zlib \
    jpeg \
    freetype \
    lcms2 \
    openjpeg \
    tiff \
    tk \
    tcl \
    harfbuzz \
    fribidi \
    libimagequant \
    libxcb \
    libpng \
    && rm -rf /var/cache/apk/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the entire application
COPY . .

# Create necessary directories
RUN mkdir -p data/chat_sessions data/user_info data/vector_store/chroma_db logs

# Expose the port Gradio will listen on
EXPOSE 7860

# Set the entrypoint with support for different commands
ENTRYPOINT ["python", "setup.py"] 