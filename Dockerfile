# syntax=docker/dockerfile:1

# Stage 1: System dependencies on Ubuntu
FROM ubuntu:22.04 AS system-deps

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
        python3.12 \
        python3.12-venv \
        build-essential \
        tesseract-ocr \
        pandoc \
        poppler-utils \
        unzip \
        curl \
        git && \
    rm -rf /var/lib/apt/lists/*

# Stage 2: Python app layer
FROM python:3.12-slim AS app

WORKDIR /app

# Install unzip for extracting dependencies.zip
RUN apt-get update && apt-get install -y unzip && rm -rf /var/lib/apt/lists/*

# Copy system dependencies from previous stage (if needed)
# (Not strictly necessary for apt-installed binaries, but left for clarity)

# Copy requirements and install Python dependencies
COPY requirements.txt ./

# Create and activate venv, then install requirements
RUN python -m venv .venv && \
    . .venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the codebase
COPY . .

# Expose Gradio default port
EXPOSE 7860

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1

# Entrypoint: use setup.py as a friendly interface for venv activation and app launch
ENTRYPOINT ["python", "setup.py"] 