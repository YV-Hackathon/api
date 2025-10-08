FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🔄 Running database migrations..."\n\
alembic upgrade head\n\
echo "✅ Migrations completed"\n\
echo "🚀 Starting FastAPI application..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips="*" --proxy-headers' > /app/start.sh && \
    chmod +x /app/start.sh

# Run migrations and start application
CMD ["/app/start.sh"]
