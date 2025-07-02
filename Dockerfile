# syntax=docker/dockerfile:1

# Production Dockerfile for NYP FYP Chatbot
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"
ENV IN_DOCKER="1"
ENV PRODUCTION="true"

WORKDIR /app

# Install system dependencies including document processing tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libpng-dev \
    cmake \
    pkg-config \
    # Document processing dependencies
    pandoc \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    # Additional dependencies for better OCR and document processing
    libtesseract-dev \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies with optimizations
COPY requirements.txt ./
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy only the necessary application files
COPY app.py ./
COPY backend.py ./
COPY infra_utils.py ./
COPY performance_utils.py ./
COPY hashing.py ./
COPY flexcyon_theme.py ./

# Copy gradio modules
COPY gradio_modules/ ./gradio_modules/

# Copy LLM modules
COPY llm/ ./llm/

# Copy static assets
COPY styles/ ./styles/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p logs

# Expose the port Gradio will listen on
EXPOSE 7860

# Set the default command to run the main application
CMD ["python", "app.py"]
