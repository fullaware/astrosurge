# FROM --platform=linux/amd64 python:3.13-slim-bookworm
FROM --platform=linux/amd64 python:3.13-slim AS builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    # Allow statements and log messages to immediately appear
    PYTHONUNBUFFERED=1 \
    # disable a pip version check to reduce run-time & log-spam
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # cache is useless in docker image, so disable to reduce image size
    PIP_NO_CACHE_DIR=1

RUN mkdir /beryl
WORKDIR /beryl
COPY requirements.txt /beryl

RUN set -ex \
    # Upgrade the package index and install security upgrades
    && apt-get update -y \
    && apt-get upgrade -y \
    # Install dependencies
    && pip install --upgrade pip \
    && pip install --target=/beryl/requirements -r requirements.txt \
    # Clean up
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*  
      

FROM --platform=linux/amd64 python:3.13-slim
WORKDIR /beryl
COPY --from=builder /beryl/requirements /usr/local/lib/python3.13/site-packages
COPY app.py /beryl
COPY /routes /beryl/routes/
COPY /config /beryl/config/
COPY /amos /beryl/amos/
COPY /templates /beryl/templates/
COPY /models /beryl/models/
COPY /utils /beryl/utils/
COPY /static/favicon.ico /beryl/static/favicon.ico
EXPOSE 8000
RUN set -ex \
    # Create a non-root user
    && addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --gid 1001 --no-create-home appuser
RUN chown -R appuser:appgroup /beryl
RUN chgrp -R 0 /beryl && chmod -R g=u /beryl
USER appuser
ENTRYPOINT ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0","--port", "8080","--workers", "3"]
# CMD python -m uvicorn main:app --host 0.0.0.0 --port 8000