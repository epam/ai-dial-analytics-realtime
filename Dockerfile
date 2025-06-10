FROM ubuntu:24.04 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3 \
                    python3-venv \
                    python3-dev \
                    pipx

RUN pipx install poetry==2.1.1
ENV POETRY=/root/.local/bin/poetry

RUN python3 -m venv .venv

ENV PATH="/app/.venv/bin:$PATH"

# fix CVE-2024-6345
RUN pip install setuptools==70.0.0 --quiet

# Install split into two steps (the dependencies and the sources)
# in order to leverage the Docker caching
COPY pyproject.toml poetry.lock poetry.toml README.md ./
RUN ${POETRY} install --no-interaction --no-ansi --no-cache --only main \
    --no-root --no-directory

COPY aidial_analytics_realtime aidial_analytics_realtime
RUN ${POETRY} install --no-interaction --no-ansi --no-cache --only main

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
    apt-get install -y python3 ca-certificates \
    # Install security fixes
    gpgv=2.4.4-2ubuntu17.2 \
    libc6=2.39-0ubuntu8.4 \
    libcap2=1:2.66-5ubuntu2.2 \
    libc-bin=2.39-0ubuntu8.4 \
    libexpat1=2.6.1-2ubuntu0.3 \
    libgnutls30t64=3.8.3-1.1ubuntu3.3 \
    liblzma5=5.6.1+really5.4.5-1ubuntu0.2 \
    libtasn1-6=4.19.0-3ubuntu0.24.04.1

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

CMD ["uvicorn", "aidial_analytics_realtime.app:app", "--host", "0.0.0.0", "--port", "5000"]
