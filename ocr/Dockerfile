# syntax=docker/dockerfile:1.4
# Use Ubuntu-based jitesoft/tesseract-ocr image (focal = Ubuntu 20.04)
FROM jitesoft/tesseract-ocr:focal

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_CACHE_DIR=/root/.cache/pip

# Set working directory
WORKDIR /app

# Switch to root for package installation
USER root

# Install Python 3 and required system dependencies
# Ubuntu 20.04 (focal) comes with Python 3.8 which is sufficient for the OCR service
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    python3-pip \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Install Spanish language pack for Tesseract using the train-lang script
# This downloads Spanish training data from the official tessdata repository
RUN train-lang spa --fast || echo "Spanish language pack installation skipped or already present"

# Verify Tesseract is accessible
RUN tesseract --version && tesseract --list-langs

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose port (must match docker-compose published port)
EXPOSE 9000

# Override the tesseract entrypoint and run the FastAPI service
ENTRYPOINT []
CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9000"]
