# CI/CD Pipeline for Monorepo (Frontend + Backend)

This repository contains a production-ready CI/CD pipeline configuration for a monorepo with:
- **Frontend**: React-based thin client (Node.js/NGINX)
- **Backend**: Python-based API server (FastAPI/Gunicorn)

## Pipeline Overview

The pipeline follows a **GitFlow-inspired workflow** with these branches:

```
Feature Branch → develop → staging → main (tags)
                     ↓         ↓         ↓
               Fast CI   Full CI   Tag Only
                    ↓         ↓
               Dev Env   Staging Env (Production Twin)
                            ↓
                    Manual Approval
                            ↓
                      main branch
                            ↓
                     Tag vX.Y.Z
                            ↓
                    Production
```

### Branch-Environment Mapping

| Branch | CI/CD | Deploy Target | Approval |
|--------|-------|---------------|----------|
| `feature/*` | Fast CI (affected services) | None | Automatic |
| `develop` | Full CI | Dev Environment | Automatic |
| `staging` | Full CI + Integration Tests | Staging (Production Twin) | **Manual** |
| `main` (tags) | Full CI + Security Scan | Production | **Manual** |

## Tooling

- **Container Runtime**: Podman (replaces Docker)
- **Deployment Target**: Amazon ECS Fargate
- **CI/CD**: GitLab CI/CD
- **Container Registry**: Amazon ECR

## Repository Structure

```
.
├── .gitlab-ci.yml              # Main pipeline configuration
├── frontend/
│   ├── Dockerfile              # Frontend container image
│   ├── nginx.conf              # NGINX reverse proxy config
│   └── package.json            # Node.js dependencies
├── backend/
│   ├── Dockerfile              # Backend container image
│   ├── pyproject.toml           # Python dependencies (Poetry)
│   └── poetry.lock             # Locked dependencies
└── ecs/
    └── task-definitions/       # ECS Fargate task definitions
        ├── frontend-staging.json
        ├── backend-staging.json
        ├── frontend-production.json
        └── backend-production.json
```

## Setup Instructions

### 1. GitLab Project Configuration

Add these **CI/CD Variables** in GitLab (Settings → CI/CD → Variables):

| Variable | Description | Masked | Protected |
|----------|-------------|--------|-----------|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key | ✓ | ✓ |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key | ✓ | ✓ |
| `AWS_ACCOUNT_ID` | Your AWS account ID | | ✓ |
| `AWS_REGION` | AWS region (e.g., `us-east-1`) | | ✓ |

### 2. AWS Infrastructure Setup

#### ECR Repositories
```bash
aws ecr create-repository --repository-name yourproject/frontend
aws ecr create-repository --repository-name yourproject/backend
```

#### ECS Clusters
```bash
# Dev Cluster
aws ecs create-cluster --cluster-name yourproject-dev-cluster

# Staging Cluster (Production Twin)
aws ecs create-cluster --cluster-name yourproject-staging-cluster

# Production Cluster
aws ecs create-cluster --cluster-name yourproject-production-cluster
```

#### ECS Services
Create ECS services for each environment:
- `frontend-dev-service` / `backend-dev-service` (dev cluster)
- `frontend-staging-service` / `backend-staging-service` (staging cluster)
- `frontend-production-service` / `backend-production-service` (production cluster)

#### IAM Roles
```bash
# Create ECS Task Execution Role
aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file://ecs-task-execution-role.json
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Update the ARN in task-definitions/*.json files
```

#### SSM Parameters (for secrets)
```bash
# Staging environment
aws ssm put-parameter --name "/yourproject/staging/DATABASE_URL" --value "your-staging-db-url" --type "SecureString"
aws ssm put-parameter --name "/yourproject/staging/SECRET_KEY" --value "your-staging-secret" --type "SecureString"

# Production environment
aws ssm put-parameter --name "/yourproject/production/DATABASE_URL" --value "your-prod-db-url" --type "SecureString"
aws ssm put-parameter --name "/yourproject/production/SECRET_KEY" --value "your-prod-secret" --type "SecureString"
```

### 3. Initialize Poetry (Backend)

```bash
cd backend
poetry install
poetry lock
```

This will generate a proper `poetry.lock` file.

## Pipeline Features

### Cost Optimization

- **Feature branches**: Only run CI for affected services
- **Docker layer caching**: Podman caches layers between builds
- **Artifact caching**: Node modules and Python virtualenv cached
- **Integration tests**: Only run on staging and production tags

### Safeguards for AI-Generated Code

1. **All code must pass CI** before merging to develop
2. **Full test suite** required for staging deployment
3. **Security scanning** (safety, bandit, pylint) before production
4. **Manual approval gates** for staging and production
5. **Integration tests** validate frontend-backend communication

### Deployment Process

#### Develop → Dev Environment
- Automatic on merge to `develop`
- Runs fast CI and deploys to dev ECS cluster
- No manual approval needed

#### Staging → Staging Environment
- **Manual approval required**
- Runs full CI + integration tests
- Deploys to staging (production twin)
- Stakeholders test here

#### Main → Production
- **Manual approval required** (tag-based)
- Only deploys from semantic version tags on `main`
- Runs full CI + security scanning
- Deploys to production ECS cluster

## Usage

### Creating a Feature Branch
```bash
git checkout -b feature/your-feature
git push origin feature/your-feature
```

The pipeline will automatically run CI for the affected services.

### Merging to Develop
```bash
git checkout develop
git merge feature/your-feature
git push origin develop
```

Automatically deploys to dev environment.

### Promoting to Staging
```bash
git checkout staging
git merge develop
git push origin staging
```

Then **manually approve** the staging deployment in GitLab CI/CD → Pipelines.

### Releasing to Production
```bash
git checkout main
git merge staging
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin main --tags
```

Then **manually approve** the production deployment in GitLab CI/CD → Pipelines.

## Monitoring

- **GitLab**: CI/CD → Pipelines, Environments
- **AWS ECS**: Service discovery, task health
- **CloudWatch**: Logs from `/ecs/frontend-*` and `/ecs/backend-*`

## Troubleshooting

### Podman in GitLab CI
If you encounter podman issues in CI, ensure your GitLab runner has:
- Podman installed
- Rootless podman configured
- Proper storage driver (overlay recommended)

### ECR Login Issues
Verify AWS credentials are correctly set in CI/CD variables.

### ECS Deployment Failures
Check:
- Task definitions are valid
- Container images exist in ECR
- IAM roles have proper permissions
- Security groups allow traffic between services

## Customization

### Changing CPU/Memory
Edit the `cpu` and `memory` fields in `ecs/task-definitions/*.json` files.

### Adding Environment Variables
Add to the `environment` array in task definition files.

### Adding Secrets
Add to the `secrets` array in task definition files, referencing AWS SSM parameters.

### Modifying Health Checks
Edit the `healthCheck` configuration in task definition files.

## Security Notes

- **Never commit secrets** to the repository
- Use AWS SSM Parameter Store for secrets
- Use IAM roles for ECS task permissions
- Enable container image scanning in ECR
- Regularly rotate AWS credentials
