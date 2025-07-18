# CyberCorp Deployment Configuration

## Overview
This document provides comprehensive deployment configurations for the CyberCorp client-server system across different environments (development, staging, production) and deployment methods.

## Deployment Environments

### 1. Development Environment
**Purpose**: Local development and testing
**Scale**: Single instance
**Data**: Synthetic/test data

### 2. Staging Environment
**Purpose**: Pre-production testing
**Scale**: Small cluster (2-3 instances)
**Data**: Production-like data subset

### 3. Production Environment
**Purpose**: Live system serving users
**Scale**: Auto-scaling cluster (2-10 instances)
**Data**: Full production data

## Infrastructure as Code

### Terraform Configuration
```hcl
# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Configuration
resource "aws_vpc" "cybercorp_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "cybercorp-vpc"
    Environment = var.environment
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "cybercorp_cluster" {
  name = "cybercorp-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# RDS Database
resource "aws_db_instance" "cybercorp_db" {
  identifier     = "cybercorp-${var.environment}"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_encrypted     = true
  
  db_name  = "cybercorp"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.cybercorp.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  tags = {
    Name        = "cybercorp-db"
    Environment = var.environment
  }
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "cybercorp_redis" {
  replication_group_id       = "cybercorp-${var.environment}"
  description                = "CyberCorp Redis Cache"
  port                       = 6379
  parameter_group_name       = "default.redis7"
  node_type                  = var.redis_node_type
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  
  subnet_group_name = aws_elasticache_subnet_group.cybercorp.name
  security_group_ids = [aws_security_group.redis.id]
  
  tags = {
    Name        = "cybercorp-redis"
    Environment = var.environment
  }
}
```

### Kubernetes Configuration

#### Namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cybercorp
  labels:
    name: cybercorp
    environment: production
```

#### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cybercorp-server
  namespace: cybercorp
  labels:
    app: cybercorp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cybercorp-server
  template:
    metadata:
      labels:
        app: cybercorp-server
    spec:
      containers:
      - name: cybercorp-server
        image: cybercorp/server:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: cybercorp-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: cybercorp-secrets
              key: redis-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: cybercorp-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: cybercorp-server-service
  namespace: cybercorp
spec:
  selector:
    app: cybercorp-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

#### Horizontal Pod Autoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cybercorp-server-hpa
  namespace: cybercorp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cybercorp-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Docker Configuration

#### Server Dockerfile
```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN useradd -r -s /bin/false cybercorp
USER cybercorp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

EXPOSE 8080

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

CMD ["python", "-m", "src.main"]
```

#### Docker Compose for Development
```yaml
version: '3.8'

services:
  server:
    build:
      context: ./cybercorp_server
      dockerfile: Dockerfile.dev
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/cybercorp_dev
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=dev-secret-key
      - ENVIRONMENT=development
    volumes:
      - ./cybercorp_server/src:/app/src
      - ./cybercorp_server/config:/app/config
    depends_on:
      - postgres
      - redis
    command: python -m src.main --reload

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=cybercorp_dev
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.dev.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - server

volumes:
  postgres_dev_data:
  redis_dev_data:
```

## Environment Configuration

### Development Environment
```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/cybercorp_dev

# Redis
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=dev-secret-key-change-in-production
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
SSL_ENABLED=false

# Monitoring
METRICS_ENABLED=true
METRICS_INTERVAL=1000
```

### Staging Environment
```bash
# .env.staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@staging-db.cybercorp.com:5432/cybercorp_staging

# Redis
REDIS_URL=redis://staging-redis.cybercorp.com:6379

# Security
JWT_SECRET=staging-secret-key
ALLOWED_ORIGINS=https://staging.cybercorp.com

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/staging.crt
SSL_KEY_PATH=/etc/ssl/private/staging.key

# Monitoring
METRICS_ENABLED=true
METRICS_INTERVAL=5000
```

### Production Environment
```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Database
DATABASE_URL=postgresql://user:password@prod-db.cybercorp.com:5432/cybercorp_prod

# Redis
REDIS_URL=redis://prod-redis.cybercorp.com:6379

# Security
JWT_SECRET=production-secret-key-from-vault
ALLOWED_ORIGINS=https://cybercorp.com,https://app.cybercorp.com

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/production.crt
SSL_KEY_PATH=/etc/ssl/private/production.key

# Monitoring
METRICS_ENABLED=true
METRICS_INTERVAL=10000
```

## CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  release:
    types: [published]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: cybercorp/server

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
    
    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: ./cybercorp_server
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to staging
      run: |
        # Deploy to staging environment
        kubectl apply -f k8s/staging/
    
    - name: Run integration tests
      run: |
        # Run integration tests against staging
        pytest tests/integration/
    
    - name: Deploy to production
      if: success()
      run: |
        # Deploy to production environment
        kubectl apply -f k8s/production/
```

## Monitoring and Alerting

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'cybercorp-server'
    static_configs:
      - targets: ['cybercorp-server:8080']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Alert Rules
```yaml
# alert_rules.yml
groups:
  - name: cybercorp.rules
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% for more than 5 minutes"

      - alert: HighMemoryUsage
        expr: memory_usage_percent > 90
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 90% for more than 3 minutes"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for more than 2 minutes"
```

## Security Configuration

### SSL/TLS Configuration
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.cybercorp.com;

    ssl_certificate /etc/ssl/certs/cybercorp.crt;
    ssl_certificate_key /etc/ssl/private/cybercorp.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    location / {
        proxy_pass http://cybercorp-server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Security Headers
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

## Backup and Recovery

### Database Backup
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="cybercorp_backup_${DATE}.sql"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > "/backups/${BACKUP_FILE}"

# Upload to S3
aws s3 cp "/backups/${BACKUP_FILE}" s3://cybercorp-backups/database/

# Clean old backups (keep 30 days)