# dep builder: builds wheels for all deps
FROM python:3.11 AS dep-builder

COPY requirements.txt /build/requirements.txt
RUN pip wheel -w /build/dist -r /build/requirements.txt



# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Creates a non-root user with an explicit UID
RUN adduser -u 1666 --disabled-password --gecos "" appuser

# Install pip requirements
COPY --from=dep-builder [ "/build/dist/*.whl", "/install/" ]
RUN pip install --no-index --no-cache-dir /install/*.whl \
    && rm -rf /install


WORKDIR /app
COPY --chown=appuser . /app


USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
EXPOSE 5000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
