FROM ubuntu:24.04 AS builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3 \
                    python3-venv \
                    python3-dev \
                    python3-pip \
                    python3-poetry

RUN python3 -m venv .venv

ENV PATH="/app/.venv/bin:$PATH"

# fix CVE-2024-6345
RUN pip install setuptools==70.0.0 --quiet

# Install split into two steps (the dependencies and the sources)
# in order to leverage the Docker caching
COPY pyproject.toml poetry.lock poetry.toml README.md ./
RUN poetry install --no-interaction --no-ansi --no-cache --only main \
    --no-root --no-directory

COPY aidial_analytics_realtime aidial_analytics_realtime
RUN poetry install --no-interaction --no-ansi --no-cache --only main

FROM ubuntu:24.04

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV MODEL_RATES='{"gpt-4":{"unit":"token","prompt_price":"0.00003","completion_price":"0.00006"},"gpt-35-turbo":{"unit":"token","prompt_price":"0.0000015","completion_price":"0.000002"},"gpt-4-32k":{"unit":"token","prompt_price":"0.00006","completion_price":"0.00012"},"text-embedding-ada-002":{"unit":"token","prompt_price":"0.0000001"},"chat-bison@001":{"unit":"char_without_whitespace","prompt_price":"0.0000005","completion_price":"0.0000005"}}'

ENV TOPIC_MODEL="davanstrien/chat_topics"
ENV TOPIC_EMBEDDINGS_MODEL="all-mpnet-base-v2"

# Install ca-certificates is required for https connection to InfluxDB
RUN apt-get update && \
    apt-get install -y python3 ca-certificates

WORKDIR /app

# Create a non-root user with an explicit UID
RUN useradd -m -u 1001 -s /bin/bash appuser
COPY --chown=appuser --from=builder /app .

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 5000

HEALTHCHECK  --interval=10s --timeout=5s --start-period=30s --retries=6 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5000/health || exit 1

# Disable syntax warnings in the hdbscan package.
ENV PYTHONWARNINGS="ignore:invalid escape sequence:SyntaxWarning"

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["uvicorn", "aidial_analytics_realtime.app:app", "--host", "0.0.0.0", "--port", "5000"]
