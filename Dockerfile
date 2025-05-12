FROM python:3.8-slim

# Install espeak for pyttsx3
RUN apt-get update && apt-get install -y espeak libespeak1 && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m appuser
USER appuser
WORKDIR /home/appuser/app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run on Render's default port
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]