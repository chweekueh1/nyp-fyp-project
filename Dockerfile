# syntax=docker/dockerfile:1
FROM python:3.11-alpine
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"
ENV IN_DOCKER="1"
ENV PRODUCTION="true"
ENV DOCKER_MODE="prod"
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV TZ=Asia/Singapore
ENV MAKEFLAGS="-j$(nproc)"
ENV PYTHONHASHSEED=random
ENV PIP_USE_PEP517=1
ARG PARALLEL_JOBS=4
ENV PIP_JOBS=${PARALLEL_JOBS}
ENV PIP_PREFER_BINARY=1
ENV PIP_ONLY_BINARY=:all:
ARG VENV_PATH=/home/appuser/.nypai-chatbot/venv
ENV VENV_PATH=${VENV_PATH}
WORKDIR /app
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
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup -s /bin/sh && \
    mkdir -p /home/appuser/.nypai-chatbot/data && \
    mkdir -p /home/appuser/.nypai-chatbot/data/cache && \
    mkdir -p /home/appuser/.nypai-chatbot/data/vector_store/chroma_db && \
    mkdir -p /home/appuser/.nypai-chatbot/data/memory_persistence && \
    mkdir -p /home/appuser/.nypai-chatbot/data/nltk_data && \
    mkdir -p /home/appuser/.nypai-chatbot/data/chat_sessions && \
    mkdir -p /home/appuser/.nypai-chatbot/data/user_info && \
    mkdir -p /home/appuser/.nypai-chatbot/uploads && \
    mkdir -p /home/appuser/.nypai-chatbot/logs && \
    mkdir -p /app/data && \
    chown -R appuser:appgroup /app && \
    chown -R appuser:appgroup /home/appuser/.nypai-chatbot && \
    chmod -R 755 /home/appuser/.nypai-chatbot && \
    chmod -R 755 /app
USER appuser
RUN python3 -m venv ${VENV_PATH}
ENV PATH="${VENV_PATH}/bin:$PATH"
ENV PYTHONPATH=/app
COPY requirements.txt ./requirements.txt
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
COPY app.py infra_utils.py performance_utils.py hashing.py flexcyon_theme.py system_prompts.py ./
COPY backend/ ./backend/
COPY gradio_modules/ ./gradio_modules/
COPY llm/ ./llm/
COPY styles/ ./styles/
COPY scripts/entrypoint.py ./
COPY infra_utils/ ./infra_utils/
EXPOSE 7860
RUN echo "[BUILD] Using ENTRYPOINT: ${VENV_PATH}/bin/python /app/entrypoint.py"
ENTRYPOINT ["sh", "-c", "${VENV_PATH}/bin/python /app/entrypoint.py \"$@\"", "--"]
CMD ["sh", "-c", "${VENV_PATH}/bin/python app.py"]
RUN echo "[BUILD] Python executable: ${VENV_PATH}/bin/python" && \
    echo "[BUILD] Python version: $(${VENV_PATH}/bin/python --version)" && \
    echo "[BUILD] Pip version: $(${VENV_PATH}/bin/pip --version)"
