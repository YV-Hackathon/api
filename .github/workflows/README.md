# GitHub Actions Workflows

This directory contains GitHub Actions workflows for building and deploying the FastAPI CMS application.

## Workflows

### `build-and-push.yml`
A workflow that builds and pushes Docker images to Google Artifact Registry with the following features:
- Builds Docker image using the project's Dockerfile
- Pushes to Google Artifact Registry
- Tags images with GitHub SHA and latest
- Triggers on push to main/develop branches and pull requests
- Manual workflow dispatch support

## Setup Instructions

### Prerequisites

1. **Google Cloud Project**: Ensure you have a GCP project with Artifact Registry enabled
2. **Service Account**: Create a service account with the following roles:
   - Artifact Registry Writer
   - Storage Object Viewer (for caching)

### Required Secrets

Add the following secrets to your GitHub repository:

1. `GCP_PROJECT_ID`: Your Google Cloud Project ID
2. `GCP_SA_KEY`: Service Account JSON key (download from GCP Console)

### Setting up Google Artifact Registry

1. Create a Docker repository in Artifact Registry:
   ```bash
   gcloud artifacts repositories create fastapi-cms \
     --repository-format=docker \
     --location=us-central1 \
     --description="FastAPI CMS Docker repository"
   ```

2. Configure Docker authentication:
   ```bash
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```

### Workflow Triggers

- **Push to main/develop**: Builds and pushes images
- **Pull Requests**: Builds images for testing
- **Manual Dispatch**: Allows manual triggering of the workflow

### Image Naming Convention

Images are tagged as:
- `us-central1-docker.pkg.dev/{PROJECT_ID}/fastapi-cms/fastapi-cms:{GITHUB_SHA}`
- `us-central1-docker.pkg.dev/{PROJECT_ID}/fastapi-cms/fastapi-cms:latest`

### Usage Examples

#### Deploying to Cloud Run
```bash
gcloud run deploy fastapi-cms \
  --image us-central1-docker.pkg.dev/{PROJECT_ID}/fastapi-cms/fastapi-cms:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Pulling the image locally
```bash
docker pull us-central1-docker.pkg.dev/{PROJECT_ID}/fastapi-cms/fastapi-cms:latest
```

### Troubleshooting

1. **Authentication Issues**: Ensure the service account has proper permissions
2. **Build Failures**: Check the Actions logs for detailed error messages
3. **Push Failures**: Verify the Artifact Registry repository exists and is accessible
