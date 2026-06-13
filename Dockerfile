FROM python:3.13-slim

# Install system dependencies for OpenCV and video streaming
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libxcb1 \
    libxkbcommon0 \
    libdbus-1-3 \
    libssl3 \
    libgomp1 \
    libjasper1 \
    libharfbuzz0b \
    libwebp7 \
    libtiff6 \
    libjasper-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "60", "app:app"]
