# Use official Python image
FROM python:3.8-slim

# Install espeak and dependencies
RUN apt-get update && apt-get install -y \
    espeak \
    libespeak-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn
RUN pip install gunicorn

# Expose port
EXPOSE 8000

# Set environment variable
ENV FLASK_SECRET_KEY=your-secret-key

# Command to run the app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]