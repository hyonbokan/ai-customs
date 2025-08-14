# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      tesseract-ocr \
      tesseract-ocr-eng \
      tesseract-ocr-chi-sim \
      tesseract-ocr-ara \
      tesseract-ocr-spa \
      tesseract-ocr-fra \
      tesseract-ocr-kor \
      tesseract-ocr-rus \
      tesseract-ocr-tha \
      tesseract-ocr-vie \
      tesseract-ocr-deu \
      tesseract-ocr-ita \
      tesseract-ocr-por \
      tesseract-ocr-nld \
      tesseract-ocr-pol \
      tesseract-ocr-slk \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with home directory
RUN addgroup --system app && adduser --system --group app --home /home/app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY backend/ .

# Create database directory and home directory with proper permissions
RUN mkdir -p /app/database && \
    mkdir -p /home/app/.EasyOCR && \
    chown -R app:app /app/database && \
    chown -R app:app /home/app

# Expose the port the app runs on
EXPOSE 8000

# Switch to the non-root user
USER app

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
