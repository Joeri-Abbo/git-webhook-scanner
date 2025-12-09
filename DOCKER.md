# Docker Deployment Guide

This guide covers how to build, run, and deploy the webhook handler using Docker.

## 🐳 Quick Start with Docker

### Using Docker Compose (Recommended)

1. **Make sure your configuration is ready:**
   ```bash
   # Copy example files if needed
   cp .env.example .env
   cp config.example.yaml config.yaml
   ```

2. **Edit `.env` with your secrets**

3. **Start the container:**
   ```bash
   docker-compose up -d
   ```

4. **View logs:**
   ```bash
   docker-compose logs -f
   ```

5. **Stop the container:**
   ```bash
   docker-compose down
   ```

### Using Docker CLI

1. **Build the image:**
   ```bash
   docker build -t webhook-handler .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name webhook-handler \
     -p 8000:8000 \
     -v $(pwd)/config.yaml:/app/config.yaml:ro \
     -v $(pwd)/events:/app/events:rw \
     --env-file .env \
     webhook-handler
   ```

3. **View logs:**
   ```bash
   docker logs -f webhook-handler
   ```

4. **Stop and remove:**
   ```bash
   docker stop webhook-handler
   docker rm webhook-handler
   ```

## 📦 Using Pre-built Images from GitHub Container Registry

Images are automatically built and published to GitHub Container Registry on every push to main/master.

### Pull and Run

```bash
# Pull the latest image
docker pull ghcr.io/joeri-abbo/git-webhook-scanner:latest

# Run the container
docker run -d \
  --name webhook-handler \
  -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/events:/app/events:rw \
  --env-file .env \
  ghcr.io/joeri-abbo/git-webhook-scanner:latest
```

### Available Tags

- `latest` - Latest build from default branch
- `main` or `master` - Latest from main/master branch
- `develop` - Latest from develop branch
- `v*.*.*` - Specific version tags (e.g., `v1.0.0`)
- `sha-<commit>` - Specific commit builds

### Using with Docker Compose

Update `docker-compose.yml` to use the pre-built image:

```yaml
services:
  webhook-handler:
    image: ghcr.io/joeri-abbo/git-webhook-scanner:latest
    # Remove the 'build' section
    # ... rest of configuration
```

## 🔐 GitHub Container Registry Authentication

For private repositories, you need to authenticate:

```bash
# Create a personal access token with read:packages scope
# Then login:
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

## 🏗️ CI/CD Pipeline

The repository includes a GitHub Actions workflow that automatically:

1. ✅ Builds Docker images on push to main/master/develop
2. ✅ Builds multi-architecture images (amd64, arm64)
3. ✅ Pushes to GitHub Container Registry
4. ✅ Tags appropriately based on branch/tag
5. ✅ Generates build attestations for security

### Workflow Triggers

- **Push to main/master/develop**: Builds and pushes with branch name tag + `latest` (for default branch)
- **Push tags (v*.*.*)**: Builds and pushes with version tags
- **Pull requests**: Builds only (no push)
- **Manual trigger**: Can be triggered manually from Actions tab

### Required Permissions

The workflow requires:
- ✅ `contents: read` - To checkout code
- ✅ `packages: write` - To push to GHCR
- ✅ `id-token: write` - For attestations

These are automatically provided by `GITHUB_TOKEN`.

## 🔧 Environment Variables

All environment variables from `.env` can be passed to the container:

### GitHub Configuration
- `GITHUB_WEBHOOK_SECRET` - Secret for webhook signature verification
- `GITHUB_API_TOKEN` - Token for GitHub API (file content fetching)

### GitLab Configuration
- `GITLAB_WEBHOOK_TOKEN` - Token for GitLab webhook auth
- `GITLAB_API_TOKEN` - Token for GitLab API

### Notification Configuration
- `NOTIFICATION_CHANNEL` - `slack` or `email`
- `SLACK_WEBHOOK_URL` - Slack webhook URL
- `EMAIL_SMTP_HOST` - SMTP server host
- `EMAIL_SMTP_PORT` - SMTP server port (default: 587)
- `EMAIL_SMTP_USER` - SMTP username
- `EMAIL_SMTP_PASSWORD` - SMTP password
- `EMAIL_FROM_ADDRESS` - From email address
- `EMAIL_TO_ADDRESSES` - Comma-separated recipient emails

## 📁 Volumes

### Required Volume Mounts

1. **config.yaml** (read-only):
   ```bash
   -v $(pwd)/config.yaml:/app/config.yaml:ro
   ```
   Your filter configuration file.

2. **events directory** (read-write):
   ```bash
   -v $(pwd)/events:/app/events:rw
   ```
   Stores received webhook events for debugging.

## 🏥 Health Checks

The container includes a built-in health check:

- **Endpoint**: `http://localhost:8000/health`
- **Interval**: Every 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Start Period**: 5 seconds

Check container health:
```bash
docker ps
# Look for health status in the STATUS column
```

## 🐛 Debugging

### View container logs
```bash
docker logs -f webhook-handler
```

### Execute commands inside container
```bash
docker exec -it webhook-handler /bin/bash
```

### Check health endpoint
```bash
curl http://localhost:8000/health
```

### Test notification
```bash
curl http://localhost:8000/test/notification
```

## 🚀 Production Deployment

### Using Kubernetes

Example deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webhook-handler
spec:
  replicas: 2
  selector:
    matchLabels:
      app: webhook-handler
  template:
    metadata:
      labels:
        app: webhook-handler
    spec:
      containers:
      - name: webhook-handler
        image: ghcr.io/joeri-abbo/git-webhook-scanner:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: webhook-secrets
        volumeMounts:
        - name: config
          mountPath: /app/config.yaml
          subPath: config.yaml
          readOnly: true
        - name: events
          mountPath: /app/events
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config
        configMap:
          name: webhook-config
      - name: events
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: webhook-handler
spec:
  selector:
    app: webhook-handler
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Using Docker Swarm

```bash
docker stack deploy -c docker-compose.yml webhook
```

### Security Best Practices

1. ✅ Run as non-root user (already configured)
2. ✅ Use secrets management for sensitive data
3. ✅ Keep images updated regularly
4. ✅ Enable read-only root filesystem when possible
5. ✅ Limit container resources (CPU, memory)
6. ✅ Use specific image tags, not `latest` in production

## 📊 Resource Requirements

### Minimum Requirements
- **CPU**: 0.25 cores
- **Memory**: 256 MB
- **Disk**: 100 MB

### Recommended for Production
- **CPU**: 0.5-1 core
- **Memory**: 512 MB - 1 GB
- **Disk**: 500 MB (for event logs)

## 🔄 Updates

### Updating to Latest Version

```bash
# Pull latest image
docker pull ghcr.io/joeri-abbo/git-webhook-scanner:latest

# Recreate container
docker-compose down
docker-compose up -d
```

### Rolling Back

```bash
# Use a specific version tag
docker pull ghcr.io/joeri-abbo/git-webhook-scanner:v1.0.0
docker-compose up -d
```
