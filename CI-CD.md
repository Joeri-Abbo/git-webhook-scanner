# CI/CD Pipeline Guide

## 📋 Overview

This repository includes automated CI/CD pipelines using GitHub Actions to build and publish Docker images to GitHub Container Registry (GHCR).

## 🔄 Automatic Builds

The Docker image is automatically built and pushed when:

### ✅ Push to Main Branches
- **Branches**: `main`, `master`, `develop`
- **Tags**: Creates `latest` tag (for default branch) and branch-specific tags
- **Action**: Builds multi-arch image (amd64, arm64) and pushes to GHCR

### ✅ Version Tags
- **Pattern**: `v*.*.*` (e.g., `v1.0.0`, `v2.1.3`)
- **Tags Created**: 
  - Full version: `v1.0.0`
  - Minor version: `1.0`
  - Major version: `1`
- **Action**: Builds and pushes with semantic version tags

### ✅ Pull Requests
- **Branches**: PRs to `main` or `master`
- **Action**: Builds image for testing (does not push)

### ✅ Manual Trigger
- **From**: GitHub Actions tab
- **Action**: Manually trigger workflow with workflow_dispatch

## 📦 Image Tags

Images are tagged as follows:

| Tag Pattern | Description | Example |
|------------|-------------|---------|
| `latest` | Latest build from default branch | `ghcr.io/joeri-abbo/git-webhook-scanner:latest` |
| `main` / `master` | Latest from main/master branch | `ghcr.io/joeri-abbo/git-webhook-scanner:main` |
| `develop` | Latest from develop branch | `ghcr.io/joeri-abbo/git-webhook-scanner:develop` |
| `v*.*.*` | Specific version tag | `ghcr.io/joeri-abbo/git-webhook-scanner:v1.0.0` |
| `<major>.<minor>` | Minor version | `ghcr.io/joeri-abbo/git-webhook-scanner:1.0` |
| `<major>` | Major version | `ghcr.io/joeri-abbo/git-webhook-scanner:1` |
| `<branch>-sha-<commit>` | Commit-specific | `ghcr.io/joeri-abbo/git-webhook-scanner:main-sha-abc123` |
| `pr-<number>` | Pull request builds | `ghcr.io/joeri-abbo/git-webhook-scanner:pr-42` |

## 🏗️ Pipeline Steps

### 1. Checkout Code
```yaml
- Checks out repository code
- Includes full git history for proper versioning
```

### 2. Setup Docker Buildx
```yaml
- Configures Docker Buildx for multi-platform builds
- Enables advanced build features and caching
```

### 3. Login to GHCR
```yaml
- Authenticates to GitHub Container Registry
- Uses automatic GITHUB_TOKEN (no manual setup needed)
```

### 4. Extract Metadata
```yaml
- Generates appropriate tags based on trigger
- Creates labels for image metadata
- Follows OCI image spec standards
```

### 5. Build and Push Image
```yaml
- Builds Docker image for multiple architectures
- Uses layer caching for faster builds
- Pushes to GHCR (except for PRs)
- Creates multi-arch manifest
```

### 6. Generate Attestations
```yaml
- Creates build provenance attestation
- Enhances supply chain security
- Verifiable with GitHub CLI or cosign
```

## 🔐 Security Features

### ✅ Automatic Token Authentication
- Uses `GITHUB_TOKEN` (automatically provided)
- No need to create or store additional secrets
- Scoped to repository permissions

### ✅ Multi-Architecture Support
- Builds for `linux/amd64` (x86_64)
- Builds for `linux/arm64` (ARM 64-bit)
- Single command pulls appropriate architecture

### ✅ Build Attestations
- Cryptographically signed build provenance
- Links image to source code commit
- Verifiable supply chain

### ✅ Security Scanning
- Images can be scanned with tools like Trivy
- Runs as non-root user
- Minimal attack surface

## 🎯 Using the Images

### Pull Latest Image
```bash
docker pull ghcr.io/joeri-abbo/git-webhook-scanner:latest
```

### Pull Specific Version
```bash
docker pull ghcr.io/joeri-abbo/git-webhook-scanner:v1.0.0
```

### Pull Specific Architecture
```bash
# Force AMD64
docker pull --platform linux/amd64 ghcr.io/joeri-abbo/git-webhook-scanner:latest

# Force ARM64
docker pull --platform linux/arm64 ghcr.io/joeri-abbo/git-webhook-scanner:latest
```

### Verify Build Provenance
```bash
# Using GitHub CLI
gh attestation verify oci://ghcr.io/joeri-abbo/git-webhook-scanner:latest --owner joeri-abbo
```

## 🚀 Creating a New Release

### Option 1: Git Tag (Recommended)
```bash
# Create and push a tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Pipeline automatically builds and publishes
```

### Option 2: GitHub Release
```bash
# Create release via GitHub UI
1. Go to repository → Releases → Create new release
2. Create new tag: v1.0.0
3. Generate release notes
4. Publish release

# Pipeline automatically builds and publishes
```

### Option 3: Manual Workflow Trigger
```bash
# From GitHub UI
1. Go to Actions tab
2. Select "Build and Push Docker Image" workflow
3. Click "Run workflow"
4. Select branch
5. Click "Run workflow"
```

## 📊 Monitoring Builds

### View Build Status
- Go to repository → Actions tab
- See all workflow runs and their status
- Click on a run to see detailed logs

### Build Badges
Add to your README.md:
```markdown
![Docker Build](https://github.com/Joeri-Abbo/git-webhook-scanner/actions/workflows/docker-build.yml/badge.svg)
```

### View Published Images
- Go to repository → Packages
- See all published container images
- View image details, tags, and sizes

## 🔧 Workflow Configuration

### Workflow File Location
```
.github/workflows/docker-build.yml
```

### Required Permissions
```yaml
permissions:
  contents: read      # Checkout code
  packages: write     # Push to GHCR
  id-token: write     # Generate attestations
```

### Environment Variables
```yaml
REGISTRY: ghcr.io
IMAGE_NAME: ${{ github.repository }}
```

## 🐛 Troubleshooting

### Build Fails on Push
1. Check Actions tab for error logs
2. Verify Dockerfile syntax
3. Ensure all required files exist
4. Check if base image is accessible

### Cannot Pull Image
1. For private repos, authenticate first:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   ```
2. Verify image exists in Packages
3. Check repository visibility settings

### Permission Denied
1. Ensure workflow has `packages: write` permission
2. Check if Actions are enabled in repository settings
3. Verify branch protection rules

### Build is Slow
1. Pipeline uses layer caching (first build is slower)
2. Subsequent builds reuse cached layers
3. Multi-arch builds take longer than single-arch

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Buildx](https://docs.docker.com/buildx/working-with-buildx/)
- [OCI Image Spec](https://github.com/opencontainers/image-spec)

## 🎓 Best Practices

1. ✅ Always tag releases with semantic versioning
2. ✅ Use specific version tags in production, not `latest`
3. ✅ Monitor build times and optimize Dockerfile
4. ✅ Regularly update base images for security
5. ✅ Use multi-stage builds when appropriate
6. ✅ Test images locally before pushing
7. ✅ Document breaking changes in releases
