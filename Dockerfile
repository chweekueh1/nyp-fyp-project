# syntax=docker/dockerfile:1

# Multi-stage Dockerfile for NYP FYP Chatbot
# Build stage with all dependencies
FROM python:3.11-alpine AS builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    zlib-dev \
    jpeg-dev \
    freetype-dev \
    libpng-dev \
    cmake \
    pkgconfig \
    # ONNX Runtime dependencies for musl
    libgomp \
    libstdc++ \
    gcc-libs \
    # Document processing dependencies
    pandoc \
    tesseract-ocr \
    tesseract-ocr-data-eng \
    poppler-utils \
    # Additional dependencies for better OCR and document processing
    tesseract-ocr-dev \
    poppler-dev

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage with Alpine Linux
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"
ENV IN_DOCKER="1"
ENV PRODUCTION="true"

WORKDIR /app

# Install runtime system dependencies
RUN apk add --no-cache \
    # Document processing runtime dependencies
    tesseract-ocr \
    tesseract-ocr-data-eng \
    poppler-utils \
    # Additional runtime dependencies
    libjpeg \
    libpng \
    freetype \
    # ONNX Runtime runtime dependencies for musl
    libgomp \
    libstdc++ \
    gcc-libs \
    # Security and performance
    ca-certificates \
    && update-ca-certificates

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only the necessary application files
COPY app.py ./
COPY backend.py ./
COPY infra_utils.py ./
COPY performance_utils.py ./
COPY hashing.py ./
COPY flexcyon_theme.py ./

# Copy backend package
COPY backend/ ./backend/

# Copy gradio modules
COPY gradio_modules/ ./gradio_modules/

# Copy LLM modules
COPY llm/ ./llm/

# Copy static assets
COPY styles/ ./styles/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p logs data

# Create non-root user for security
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Change ownership of app directory
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose the port Gradio will listen on
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7860/')" || exit 1

# Set the default command to run the main application
CMD ["python", "app.py"]
