# FROM --platform=linux/amd64 python:3.13-slim-bookworm
FROM --platform=linux/amd64 python:3.13-slim AS builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    # Allow statements and log messages to immediately appear
    PYTHONUNBUFFERED=1 \
    # disable a pip version check to reduce run-time & log-spam
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # cache is useless in docker image, so disable to reduce image size
    PIP_NO_CACHE_DIR=1

RUN mkdir /astrosurge
WORKDIR /astrosurge
COPY requirements.txt /astrosurge

RUN set -ex \
    # Upgrade the package index and install security upgrades
    && apt-get update -y \
    && apt-get upgrade -y \
    # Install dependencies
    && pip install --upgrade pip \
    && pip install --target=/astrosurge/requirements -r requirements.txt \
    # Clean up
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*  
      

FROM --platform=linux/amd64 python:3.13-slim
WORKDIR /astrosurge
COPY --from=builder /astrosurge/requirements /usr/local/lib/python3.13/site-packages
COPY app.py /astrosurge
COPY /routes /astrosurge/routes/
COPY /config /astrosurge/config/
COPY /amos /astrosurge/amos/
COPY /templates /astrosurge/templates/
COPY /models /astrosurge/models/
COPY /utils /astrosurge/utils/
COPY /static/favicon.ico /astrosurge/static/favicon.ico
EXPOSE 8000
RUN set -ex \
    # Create a non-root user
    && addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --gid 1001 --no-create-home appuser
RUN chown -R appuser:appgroup /astrosurge
RUN chgrp -R 0 /astrosurge && chmod -R g=u /astrosurge
USER appuser
ENTRYPOINT ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0","--port", "8080","--workers", "3"]
# CMD python -m uvicorn main:app --host 0.0.0.0 --port 8000