FROM python:3.13-slim

# Install system dependencies for OpenCV and GUI support
RUN apt-get update && apt-get install -y \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libxcb1 \
    libxkbcommon0 \
    libdbus-1-3 \
    libssl3 \
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
