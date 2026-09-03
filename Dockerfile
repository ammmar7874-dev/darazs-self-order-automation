# Dockerfile for DarazBot Pro Automation Suite
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8765

WORKDIR /app

# Install system dependencies for Playwright & Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    ca-certificates \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser binaries
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy full application code
COPY . .

# Create data directories
RUN mkdir -p data/browser_profiles

# Expose server port
EXPOSE 8765

# Start FastAPI Application
CMD ["python", "-m", "backend.main"]
