FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy all source code first
COPY pyproject.toml .
COPY src/ ./src/
COPY webui/ ./webui/

# Tell the app where webui lives (fixed path in Docker)
ENV ASTROSURGE_WEBUI_DIR=/app/webui

# Install dependencies (non-editable for clean Docker deployment)
RUN pip install --no-cache-dir . && \
    pip install --no-cache-dir fastapi uvicorn[standard] jinja2 aiofiles

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "astrosurge.web.app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
