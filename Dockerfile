# dep builder: builds wheels for all deps
FROM python:3.11 AS dep-builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install "poetry==1.6.1"

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml poetry.lock .

RUN poetry export -f requirements.txt | pip install -r /dev/stdin


# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV MODEL_RATES='{"gpt-4":{"unit":"token","prompt_price":"0.00003","completion_price":"0.00006"},"gpt-35-turbo":{"unit":"token","prompt_price":"0.0000015","completion_price":"0.000002"},"gpt-4-32k":{"unit":"token","prompt_price":"0.00006","completion_price":"0.00012"},"text-embedding-ada-002":{"unit":"token","prompt_price":"0.0000001"},"chat-bison@001":{"unit":"char_without_whitespace","prompt_price":"0.0000005","completion_price":"0.0000005"}}'

# Creates a non-root user with an explicit UID
RUN adduser -u 1666 --disabled-password --gecos "" appuser

# Install pip requirements
COPY --from=dep-builder /opt/venv /opt/venv

WORKDIR /
COPY --chown=appuser ./ai_dial_analytics_realtime /ai_dial_analytics_realtime
COPY --chown=appuser ./topic_model /topic_model

ENV PATH="/opt/venv/bin:$PATH"


USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
EXPOSE 5000
CMD ["uvicorn", "ai_dial_analytics_realtime.app:app", "--host", "0.0.0.0", "--port", "5000"]
