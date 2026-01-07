FROM python:3.7-slim

WORKDIR /app

# Install system dependencies required for TensorFlow, OpenCV, and image processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip==20.2.4
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directory if it doesn't exist
RUN mkdir -p storage/model

# Expose port (Elastic Beanstalk uses port 8000, ECS can use 5000)
EXPOSE 8000

# Use gunicorn to run the Flask app
# Elastic Beanstalk expects port 8000, but we can configure it
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "300", "main:app"]



