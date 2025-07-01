# syntax=docker/dockerfile:1

# Use Python 3.12 slim for both building and runtime
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"

WORKDIR /app

# Install system dependencies for building and running Python packages
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
        tesseract-ocr \
        pandoc \
        poppler-utils \
        unzip \
        curl \
        git \
        # Runtime libraries (using correct package names for Debian Bookworm)
        libffi8 \
        libssl3 \
        zlib1g \
        libjpeg62-turbo \
        libfreetype6 \
        liblcms2-2 \
        libopenjp2-7 \
        libtiff6 \
        tk \
        tcl \
        libharfbuzz0b \
        libfribidi0 \
        libimagequant0 \
        libxcb1 \
        libpng16-16 \
        && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Expose the port Gradio will listen on
EXPOSE 7860

# Set the entrypoint with support for different commands
ENTRYPOINT ["python", "setup.py"] 