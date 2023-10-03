# dep-builder: builds venv with all deps
FROM ubuntu:22.04 AS dep-builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y python3.11 \
                       python3.11-venv \
                       python3.11-dev \
                       python3-pip && \
    python3.11 -m pip install "poetry==1.6.1" && \
    python3.11 -m venv /opt/venv


ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml poetry.lock .
RUN poetry export -f requirements.txt | python3.11 -m pip install -r /dev/stdin


FROM ubuntu:22.04

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV MODEL_RATES='{"gpt-4":{"unit":"token","prompt_price":"0.00003","completion_price":"0.00006"},"gpt-35-turbo":{"unit":"token","prompt_price":"0.0000015","completion_price":"0.000002"},"gpt-4-32k":{"unit":"token","prompt_price":"0.00006","completion_price":"0.00012"},"text-embedding-ada-002":{"unit":"token","prompt_price":"0.0000001"},"chat-bison@001":{"unit":"char_without_whitespace","prompt_price":"0.0000005","completion_price":"0.0000005"}}'

ENV TOPIC_MODEL="davanstrien/chat_topics"
ENV TOPIC_EMBEDDINGS_MODEL="all-mpnet-base-v2"

# Creates a non-root user with an explicit UID
RUN adduser -u 1001 --disabled-password --gecos "" appuser

WORKDIR /

# Install ca-certificates is required for https connection to InfluxDB
RUN apt-get update && \
    apt-get install -y python3.11 ca-certificates

COPY --from=dep-builder --chown=appuser /opt/venv /opt/venv
COPY --chown=appuser ./aidial_analytics_realtime /aidial_analytics_realtime

ENV PATH="/opt/venv/bin:$PATH"


USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
EXPOSE 5000
CMD ["uvicorn", "aidial_analytics_realtime.app:app", "--host", "0.0.0.0", "--port", "5000"]
