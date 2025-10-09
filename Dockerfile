FROM python:3.13-slim

WORKDIR /app

# Install system dependencies (this layer will be cached unless system deps change)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (this layer will be cached unless requirements.txt changes)
RUN pip install --no-cache-dir -r requirements.txt

# Create startup script early (this layer will be cached)
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🔄 Running database migrations..."\n\
alembic upgrade head\n\
echo "✅ Migrations completed"\n\
echo "🚀 Starting FastAPI application..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips="*" --proxy-headers' > /app/start.sh && \
    chmod +x /app/start.sh

# Copy application code last (this layer changes most frequently)
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start application
CMD ["/app/start.sh"]
