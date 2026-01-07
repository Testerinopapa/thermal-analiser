FROM python:3.7-slim

WORKDIR /app

# Install system dependencies required for TensorFlow, OpenCV, and image processing
# Clean up in same layer to save space
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Copy requirements first for better Docker layer caching
# Try production requirements first, fallback to regular requirements.txt
COPY requirements-prod.txt requirements.txt ./
RUN if [ -f requirements-prod.txt ]; then \
        echo "Using requirements-prod.txt"; \
        cp requirements-prod.txt requirements.txt; \
    elif [ ! -f requirements.txt ]; then \
        echo "ERROR: No requirements file found!"; \
        exit 1; \
    else \
        echo "Using requirements.txt"; \
    fi

# Upgrade pip and install Python dependencies
# Pin pip version compatible with Python 3.7
# Clean up pip cache and temp files to save space
# Remove build tools after installation to save space
RUN pip install --no-cache-dir --upgrade pip==20.2.4 \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn==20.1.0 \
    && python -c "import gunicorn; print('Gunicorn installed successfully')" \
    && apt-get update \
    && apt-get remove -y gcc g++ \
    && apt-get autoremove -y \
    && apt-get clean \
    && pip cache purge \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/* \
    && rm -rf /root/.cache/pip \
    && find /usr/local -name "*.pyc" -delete \
    && find /usr/local -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true \
    && python -c "import gunicorn; print('Gunicorn still available after cleanup')" \
    && which gunicorn || python -m gunicorn --version || echo "Gunicorn check complete"

# Copy application code
COPY . .

# Create storage directory if it doesn't exist
RUN mkdir -p storage/model

# Expose port (Elastic Beanstalk uses port 8000)
EXPOSE 8000

# Health check (using urllib instead of requests to avoid extra dependency)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Use gunicorn to run the Flask app
# Elastic Beanstalk expects port 8000
# Use python -m gunicorn to ensure it's found in PATH
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "300", "main:app"]

