FROM ubuntu:24.04 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        python3 \
        python3-venv \
        python3-dev \
        pipx

RUN pipx install poetry==2.1.1
ENV POETRY=/root/.local/bin/poetry

RUN python3 -m venv .venv

ENV PATH="/app/.venv/bin:$PATH"

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

CMD ["uvicorn", "aidial_analytics_realtime.app:app", "--host", "0.0.0.0", "--port", "5000"]
