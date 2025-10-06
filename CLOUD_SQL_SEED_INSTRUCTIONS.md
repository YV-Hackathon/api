# Running Seed Script with Cloud SQL

Since your database is hosted on Google Cloud SQL, you'll need to connect to it remotely. Here are several methods to run the seed script:

## Method 1: Direct Connection (Recommended)

### 1. Get Database Connection Details
Your Cloud SQL instance details:
- **Host**: `34.71.154.21`
- **Port**: `5432`
- **Database**: `fastapi_cms`
- **Username**: `fastapi`
- **Password**: `REDACTED`

### 2. Update Environment Configuration
Create or update your `.env` file:

```bash
# Copy the example file
cp env.example .env
```

Edit `.env` with your Cloud SQL details:
```bash
DATABASE_URL=postgresql://fastapi:REDACTED@34.71.154.21:5432/fastapi_cms
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations
```bash
alembic upgrade head
```

### 5. Run the Seed Script
```bash
python seed_data.py
```

## Method 2: Using Cloud SQL Proxy (More Secure)

### 1. Install Cloud SQL Proxy
```bash
# Download and install the proxy
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.amd64
chmod +x cloud_sql_proxy
sudo mv cloud_sql_proxy /usr/local/bin/
```

### 2. Start the Proxy
```bash
# Get your connection name
gcloud sql instances describe fastapi-postgres-dev-86429d2 --format="value(connectionName)"

# Start the proxy (replace with your actual connection name)
cloud_sql_proxy -instances=YOUR_PROJECT_ID:us-central1:fastapi-postgres-dev-86429d2=tcp:5432
```

### 3. Update .env for Local Connection
```bash
DATABASE_URL=postgresql://fastapi:REDACTED@localhost:5432/fastapi_cms
```

### 4. Run Migrations and Seed Script
```bash
alembic upgrade head
python seed_data.py
```

## Method 3: Using Docker (Isolated Environment)

### 1. Create a Dockerfile for seeding
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run migrations and seed script
CMD ["sh", "-c", "alembic upgrade head && python seed_data.py"]
```

### 2. Build and run the container
```bash
# Build the image
docker build -t fastapi-seed .

# Run with environment variables
docker run --rm \
  -e DATABASE_URL="postgresql://fastapi:REDACTED@34.71.154.21:5432/fastapi_cms" \
  -e SECRET_KEY="your-secret-key-here" \
  fastapi-seed
```

## Method 4: Using Cloud Shell

### 1. Open Cloud Shell
```bash
gcloud cloud-shell ssh
```

### 2. Clone your repository
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo/fastapi-cms
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set environment variables
```bash
export DATABASE_URL="postgresql://fastapi:REDACTED@34.71.154.21:5432/fastapi_cms"
export SECRET_KEY="your-secret-key-here"
```

### 5. Run migrations and seed
```bash
alembic upgrade head
python seed_data.py
```

## Method 5: Using Cloud Run Job (Production Approach)

### 1. Create a Cloud Run Job configuration
```yaml
# cloudrun-job.yaml
apiVersion: run.googleapis.com/v1
kind: Job
metadata:
  name: fastapi-seed-job
  annotations:
    run.googleapis.com/launch-stage: BETA
spec:
  template:
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/YOUR_PROJECT_ID/fastapi-cms:latest
            command: ["python", "seed_data.py"]
            env:
            - name: DATABASE_URL
              value: "postgresql://fastapi:REDACTED@34.71.154.21:5432/fastapi_cms"
            - name: SECRET_KEY
              value: "your-secret-key-here"
```

### 2. Deploy and run the job
```bash
gcloud run jobs replace cloudrun-job.yaml --region=us-central1
gcloud run jobs execute fastapi-seed-job --region=us-central1
```

## Troubleshooting

### Connection Issues
1. **Check firewall rules**: Ensure your IP is allowed to connect to Cloud SQL
2. **Verify credentials**: Double-check username, password, and database name
3. **Test connection**: Use `psql` to test the connection:
   ```bash
   psql "postgresql://fastapi:REDACTED@34.71.154.21:5432/fastapi_cms"
   ```

### Migration Issues
1. **Check Alembic configuration**: Ensure `alembic.ini` points to the correct database
2. **Verify table creation**: Check if tables exist before seeding
3. **Check logs**: Look for specific error messages in the output

### Security Considerations
1. **Use Cloud SQL Proxy** for production environments
2. **Rotate passwords** regularly
3. **Restrict IP access** to only necessary sources
4. **Use IAM authentication** when possible

## Quick Start (Recommended)

For the fastest setup, use Method 1:

```bash
# 1. Set up environment
cp env.example .env
echo 'DATABASE_URL=postgresql://fastapi:REDACTED@34.71.154.21:5432/fastapi_cms' >> .env
echo 'SECRET_KEY=your-secret-key-here' >> .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
alembic upgrade head

# 4. Run seed script
python seed_data.py
```

This will populate your Cloud SQL database with all the sample data!
