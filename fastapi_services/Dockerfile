FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Download Spacy model
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1.tar.gz

# Copy FastAPI services and ML models
# Note: ML models will be mounted in docker-compose during dev, 
# but this is good for prod builds.
COPY . .

# Uvicorn will be run via docker-compose command
EXPOSE 8001
