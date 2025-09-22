# DuckBot v4.2 Administrator Guide

## Table of Contents
- [Overview](#overview)
- [System Deployment](#system-deployment)
- [Performance Optimization](#performance-optimization)
- [Security Configuration](#security-configuration)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Backup and Recovery](#backup-and-recovery)
- [Scaling and High Availability](#scaling-and-high-availability)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

This guide provides comprehensive information for system administrators responsible for deploying, managing, and maintaining DuckBot v4.2 in production environments.

### Administrator Responsibilities
- System deployment and configuration
- Performance monitoring and optimization
- Security hardening and compliance
- Backup and disaster recovery
- Scaling and high availability
- User management and access control
- System updates and maintenance

### Architecture Overview

```
DuckBot v4.2 Production Architecture
├── Load Balancer
├── Web Servers (Multiple instances)
├── Application Servers
├── AI Model Servers
├── Database Cluster
├── Cache Layer (Redis)
├── Message Queue (RabbitMQ)
├── Monitoring Stack
└── Backup Storage
```

## System Deployment

### 1. System Requirements

#### Hardware Requirements
- **CPU**: 8+ cores (16+ recommended for production)
- **RAM**: 32GB+ (64GB+ recommended for large deployments)
- **Storage**: 500GB SSD (1TB+ recommended)
- **GPU**: NVIDIA RTX 3090 or better (optional but recommended)
- **Network**: 1Gbps+ connection

#### Software Requirements
- **Operating System**: Ubuntu 20.04 LTS or CentOS 8+
- **Python**: 3.9+ (3.10+ recommended)
- **Database**: PostgreSQL 13+ or MongoDB 5.0+
- **Cache**: Redis 6.0+
- **Message Queue**: RabbitMQ 3.9+
- **Web Server**: Nginx 1.18+
- **Container**: Docker 20.10+
- **Orchestration**: Kubernetes 1.20+ (optional)

### 2. Production Deployment

#### Option 1: Docker Deployment

##### Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  duckbot-web:
    build: .
    ports:
      - "8787:8787"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/duckbot
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672
    depends_on:
      - db
      - redis
      - rabbitmq
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  duckbot-ai:
    build: .
    command: python start_ai_ecosystem.py
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/duckbot
      - REDIS_URL=redis://redis:6379
      - AI_PROVIDER=lm_studio
      - LM_STUDIO_URL=http://lm-studio:1234/v1
    depends_on:
      - db
      - redis
    volumes:
      - ./models:/app/models
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: '4.0'

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=duckbot
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  rabbitmq:
    image: rabbitmq:3.9-management
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest
    ports:
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - duckbot-web
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
```

##### Dockerfile
```dockerfile
# Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 duckbot && chown -R duckbot:duckbot /app
USER duckbot

# Expose port
EXPOSE 8787

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8787/api/v1/health || exit 1

# Start application
CMD ["python", "start_ecosystem.py"]
```

#### Option 2: Kubernetes Deployment

##### Kubernetes Manifests
```yaml
# duckbot-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: duckbot-web
  labels:
    app: duckbot
    tier: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: duckbot
      tier: web
  template:
    metadata:
      labels:
        app: duckbot
        tier: web
    spec:
      containers:
      - name: duckbot-web
        image: duckbot:latest
        ports:
        - containerPort: 8787
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: duckbot-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: duckbot-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8787
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/ready
            port: 8787
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: duckbot-web-service
spec:
  selector:
    app: duckbot
    tier: web
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8787
  type: LoadBalancer

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: duckbot-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - duckbot.example.com
    secretName: duckbot-tls
  rules:
  - host: duckbot.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: duckbot-web-service
            port:
              number: 80
```

##### Horizontal Pod Autoscaler
```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: duckbot-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: duckbot-web
  minReplicas: 3
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

### 3. Database Setup

#### PostgreSQL Configuration
```sql
-- Create database and user
CREATE DATABASE duckbot;
CREATE USER duckbot_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE duckbot TO duckbot_user;

-- Create tables
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP
);

CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(255),
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    model VARCHAR(100) NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE memory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, key)
);

-- Create indexes
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_memory_user_key ON memory(user_id, key);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
```

#### MongoDB Configuration
```javascript
// MongoDB setup script
use duckbot;

// Create collections
db.createCollection("users");
db.createCollection("sessions");
db.createCollection("conversations");
db.createCollection("memory");
db.createCollection("workflows");

// Create indexes
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });
db.sessions.createIndex({ "session_id": 1 }, { unique: true });
db.sessions.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });
db.conversations.createIndex({ "user_id": 1, "created_at": -1 });
db.memory.createIndex({ "user_id": 1, "key": 1 }, { unique: true });
db.memory.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });
```

### 4. Reverse Proxy Configuration

#### Nginx Configuration
```nginx
# /etc/nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    # Upstream servers
    upstream duckbot_backend {
        server 127.0.0.1:8787;
        keepalive 32;
    }

    # HTTP server
    server {
        listen 80;
        server_name duckbot.example.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name duckbot.example.com;

        # SSL configuration
        ssl_certificate /etc/letsencrypt/live/duckbot.example.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/duckbot.example.com/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 1d;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # Client configuration
        client_max_body_size 100M;
        client_body_timeout 30s;
        client_header_timeout 10s;

        # Proxy configuration
        location / {
            proxy_pass http://duckbot_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Port $server_port;

            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;

            # Buffer settings
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
            proxy_busy_buffers_size 8k;
        }

        # WebSocket support
        location /ws {
            proxy_pass http://duckbot_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location /static {
            alias /app/static;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

## Performance Optimization

### 1. System-Level Optimization

#### Kernel Tuning
```bash
# /etc/sysctl.conf
# Network optimization
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.ipv4.tcp_congestion_control = bbr
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 4096

# File system optimization
fs.file-max = 100000
fs.inotify.max_user_watches = 524288

# Memory optimization
vm.swappiness = 10
vm.dirty_ratio = 60
vm.dirty_background_ratio = 2

# Apply settings
sysctl -p
```

#### Resource Limits
```bash
# /etc/security/limits.conf
duckbot soft nofile 65536
duckbot hard nofile 65536
duckbot soft nproc 4096
duckbot hard nproc 4096
duckbot soft memlock unlimited
duckbot hard memlock unlimited
```

### 2. Application-Level Optimization

#### Python Optimization
```python
# config/optimization.py
import asyncio
import uvloop

# Set event loop policy for better performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Connection pooling settings
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_TIMEOUT = 30

# Redis connection settings
REDIS_CONNECTION_POOL_SIZE = 50
REDIS_MAX_CONNECTIONS = 100

# Async settings
ASYNC_THREAD_POOL_SIZE = 4
ASYNC_MAX_WORKERS = 10

# Cache settings
CACHE_DEFAULT_TIMEOUT = 3600
CACHE_MAX_ENTRIES = 10000

# Rate limiting settings
RATE_LIMIT_REQUESTS_PER_MINUTE = 100
RATE_LIMIT_BURST_SIZE = 10
```

#### Database Optimization
```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.asyncio import create_async_engine

# PostgreSQL optimization
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)

# Query optimization
async def optimized_query():
    # Use indexes effectively
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
                SELECT id, message, response, created_at
                FROM conversations
                WHERE user_id = :user_id
                AND created_at > :cutoff_date
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"user_id": user_id, "cutoff_date": cutoff_date, "limit": limit}
        )
    return result.fetchall()
```

### 3. Cache Optimization

#### Redis Configuration
```redis
# /etc/redis/redis.conf
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
timeout 300
tcp-keepalive 60
tcp-backlog 511
```

#### Cache Strategy Implementation
```python
from duckbot.core.cache_manager import CacheManager

class OptimizedCacheManager(CacheManager):
    def __init__(self):
        super().__init__()
        self.local_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0}

    async def get_with_fallback(self, key, fallback_func, ttl=3600):
        """Get from cache with fallback to function"""
        # Try local cache first
        if key in self.local_cache:
            self.cache_stats["hits"] += 1
            return self.local_cache[key]

        # Try Redis cache
        cached = await self.get_cached_response(key)
        if cached:
            self.cache_stats["hits"] += 1
            self.local_cache[key] = cached
            return cached

        # Fallback to function
        self.cache_stats["misses"] += 1
        result = await fallback_func()

        # Cache the result
        await self.cache_response(key, result, ttl)
        self.local_cache[key] = result

        return result

    def get_cache_stats(self):
        """Get cache performance statistics"""
        total = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total if total > 0 else 0
        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": hit_rate,
            "total_requests": total
        }
```

### 4. AI Model Optimization

#### Model Loading Strategy
```python
from duckbot.core.dynamic_model_manager import DynamicModelManager

class OptimizedModelManager(DynamicModelManager):
    def __init__(self):
        super().__init__()
        self.model_cache = {}
        self.usage_stats = {}

    async def get_optimal_model(self, task_type, complexity):
        """Get optimal model based on task and system resources"""
        system_resources = await self.get_system_resources()

        # Model selection logic
        if complexity == "low" and system_resources["memory_available"] < 8192:
            return "phi-3-mini"
        elif complexity == "medium" and system_resources["memory_available"] < 16384:
            return "qwen2.5-7b"
        elif complexity == "high":
            return "qwen3-30b"
        else:
            return "nemotron-49b"

    async def manage_model_pool(self):
        """Manage model pool for optimal performance"""
        while True:
            system_resources = await self.get_system_resources()

            # Unload unused models
            for model_id, stats in self.usage_stats.items():
                if (time.time() - stats["last_used"]) > 900:  # 15 minutes
                    await self.unload_model(model_id)
                    del self.usage_stats[model_id]

            # Load frequently used models
            for model_id, stats in self.usage_stats.items():
                if stats["usage_count"] > 10 and model_id not in self.model_cache:
                    await self.load_model(model_id)

            await asyncio.sleep(60)  # Check every minute
```

## Security Configuration

### 1. Authentication and Authorization

#### JWT Configuration
```python
# config/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets

class SecurityManager:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = secrets.token_urlsafe(32)
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    def create_access_token(self, data: dict):
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except JWTError:
            return None

    def hash_password(self, password: str) -> str:
        """Hash password"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return self.pwd_context.verify(plain_password, hashed_password)
```

#### API Key Management
```python
class APIKeyManager:
    def __init__(self):
        self.api_keys = {}

    def generate_api_key(self, user_id: str, permissions: list = None):
        """Generate API key for user"""
        api_key = f"dk_{secrets.token_urlsafe(32)}"
        key_hash = self.hash_api_key(api_key)

        self.api_keys[key_hash] = {
            "user_id": user_id,
            "permissions": permissions or ["read", "write"],
            "created_at": datetime.utcnow(),
            "last_used": None,
            "is_active": True
        }

        return api_key

    def validate_api_key(self, api_key: str):
        """Validate API key"""
        key_hash = self.hash_api_key(api_key)
        key_data = self.api_keys.get(key_hash)

        if key_data and key_data["is_active"]:
            key_data["last_used"] = datetime.utcnow()
            return key_data

        return None

    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
```

### 2. Network Security

#### Firewall Configuration
```bash
# /etc/iptables/rules.v4
# Clear existing rules
*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]

# Allow loopback
-A INPUT -i lo -j ACCEPT

# Allow established connections
-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Allow SSH (port 22)
-A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -j ACCEPT

# Allow HTTP/HTTPS (ports 80, 443)
-A INPUT -p tcp --dport 80 -m conntrack --ctstate NEW -j ACCEPT
-A INPUT -p tcp --dport 443 -m conntrack --ctstate NEW -j ACCEPT

# Allow internal services
-A INPUT -s 10.0.0.0/8 -p tcp --dport 8787 -j ACCEPT
-A INPUT -s 172.16.0.0/12 -p tcp --dport 8787 -j ACCEPT
-A INPUT -s 192.168.0.0/16 -p tcp --dport 8787 -j ACCEPT

# Rate limiting
-A INPUT -p tcp --dport 80 -m connlimit --connlimit-above 50 -j DROP
-A INPUT -p tcp --dport 443 -m connlimit --connlimit-above 50 -j DROP

# Log dropped packets
-A INPUT -j LOG --log-prefix "iptables-dropped: " --log-level 4

COMMIT
```

#### SSL/TLS Configuration
```nginx
# Strong SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers off;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_ecdh_curve X25519:secp384r1;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
```

### 3. Application Security

#### Input Validation
```python
from pydantic import BaseModel, validator
import re

class ChatRequest(BaseModel):
    message: str
    model: str = "qwen3-coder"
    max_tokens: int = 512
    temperature: float = 0.7

    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 10000:
            raise ValueError('Message too long')

        # Remove potential harmful content
        v = re.sub(r'<[^>]*>', '', v)  # Remove HTML tags
        v = re.sub(r'[<>]', '', v)    # Remove angle brackets

        return v.strip()

    @validator('model')
    def validate_model(cls, v):
        allowed_models = ['qwen3-coder', 'nemotron-49b', 'gemma-12b']
        if v not in allowed_models:
            raise ValueError(f'Invalid model: {v}')
        return v

    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if v < 1 or v > 4096:
            raise ValueError('max_tokens must be between 1 and 4096')
        return v

    @validator('temperature')
    def validate_temperature(cls, v):
        if v < 0.0 or v > 2.0:
            raise ValueError('temperature must be between 0.0 and 2.0')
        return v
```

#### Rate Limiting
```python
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
import time

class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.limits = {
            "api_key": {"requests": 1000, "window": 3600},  # 1000 requests per hour
            "user": {"requests": 100, "window": 3600},      # 100 requests per hour
            "ip": {"requests": 50, "window": 3600}         # 50 requests per hour
        }

    async def check_rate_limit(self, key: str, limit_type: str = "api_key"):
        """Check if request is within rate limit"""
        if limit_type not in self.limits:
            raise ValueError(f"Invalid limit type: {limit_type}")

        limit = self.limits[limit_type]
        now = time.time()
        window_start = now - limit["window"]

        if key not in self.requests:
            self.requests[key] = []

        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]

        # Check if over limit
        if len(self.requests[key]) >= limit["requests"]:
            reset_time = self.requests[key][0] + limit["window"]
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again after {datetime.fromtimestamp(reset_time)}"
            )

        # Record request
        self.requests[key].append(now)
        return True
```

### 4. Data Protection

#### Encryption Configuration
```python
from cryptography.fernet import Fernet
import base64
import os

class DataEncryption:
    def __init__(self):
        # Generate or load encryption key
        self.key = self._get_or_generate_key()
        self.fernet = Fernet(self.key)

    def _get_or_generate_key(self):
        """Get or generate encryption key"""
        key_file = "data/encryption_key.key"

        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs("data", exist_ok=True)
            with open(key_file, "wb") as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def encrypt_file(self, file_path: str):
        """Encrypt file contents"""
        with open(file_path, "rb") as f:
            data = f.read()

        encrypted_data = self.fernet.encrypt(data)

        with open(file_path + ".encrypted", "wb") as f:
            f.write(encrypted_data)

        # Securely delete original file
        os.remove(file_path)

    def decrypt_file(self, encrypted_file_path: str):
        """Decrypt file contents"""
        with open(encrypted_file_path, "rb") as f:
            encrypted_data = f.read()

        decrypted_data = self.fernet.decrypt(encrypted_data)

        output_path = encrypted_file_path.replace(".encrypted", "")
        with open(output_path, "wb") as f:
            f.write(decrypted_data)

        return output_path
```

## Monitoring and Maintenance

### 1. System Monitoring

#### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'duckbot'
    static_configs:
      - targets: ['localhost:8787']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['localhost:9121']
```

#### Alert Rules
```yaml
# alert_rules.yml
groups:
  - name: duckbot_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is {{ $value }}% on instance {{ $labels.instance }}"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value }}% on instance {{ $labels.instance }}"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "Service {{ $labels.instance }} is down"

      - alert: DatabaseConnectionsHigh
        expr: pg_stat_database_numbackends / pg_settings_max_connections * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "Database connections are at {{ $value }}% of maximum"
```

### 2. Application Monitoring

#### Custom Metrics
```python
from prometheus_client import Counter, Histogram, Gauge, Info
import time

class DuckBotMetrics:
    def __init__(self):
        # Request metrics
        self.request_count = Counter('duckbot_requests_total', 'Total requests', ['method', 'endpoint'])
        self.request_duration = Histogram('duckbot_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
        self.active_requests = Gauge('duckbot_active_requests', 'Active requests')

        # AI metrics
        self.ai_requests_total = Counter('duckbot_ai_requests_total', 'AI requests total', ['model', 'provider'])
        self.ai_request_duration = Histogram('duckbot_ai_request_duration_seconds', 'AI request duration', ['model'])
        self.tokens_used = Counter('duckbot_tokens_used_total', 'Tokens used total', ['model'])

        # Error metrics
        self.error_count = Counter('duckbot_errors_total', 'Total errors', ['type', 'endpoint'])

        # System metrics
        self.models_loaded = Gauge('duckbot_models_loaded', 'Models currently loaded')
        self.memory_usage = Gauge('duckbot_memory_usage_bytes', 'Memory usage in bytes')
        self.cpu_usage = Gauge('duckbot_cpu_usage_percent', 'CPU usage percentage')

        # Business metrics
        self.conversations_total = Counter('duckbot_conversations_total', 'Total conversations')
        self.active_users = Gauge('duckbot_active_users', 'Active users')

        # Service info
        self.service_info = Info('duckbot_service_info', 'Service information')
        self.service_info.info({
            'version': '4.2.0',
            'build': 'production',
            'environment': 'production'
        })

    def record_request(self, method: str, endpoint: str, duration: float):
        """Record HTTP request"""
        self.request_count.labels(method=method, endpoint=endpoint).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_ai_request(self, model: str, provider: str, duration: float, tokens: int):
        """Record AI request"""
        self.ai_requests_total.labels(model=model, provider=provider).inc()
        self.ai_request_duration.labels(model=model).observe(duration)
        self.tokens_used.labels(model=model).inc(tokens)

    def record_error(self, error_type: str, endpoint: str):
        """Record error"""
        self.error_count.labels(type=error_type, endpoint=endpoint).inc()

    def update_system_metrics(self, memory_usage: int, cpu_usage: float, models_loaded: int):
        """Update system metrics"""
        self.memory_usage.set(memory_usage)
        self.cpu_usage.set(cpu_usage)
        self.models_loaded.set(models_loaded)

    def update_business_metrics(self, conversations_count: int, active_users_count: int):
        """Update business metrics"""
        self.conversations_total.inc(conversations_count)
        self.active_users.set(active_users_count)
```

#### Health Checks
```python
from fastapi import FastAPI, HTTPException
from duckbot.core.health_checker import HealthChecker

class HealthChecker:
    def __init__(self):
        self.checks = {
            "database": self.check_database,
            "redis": self.check_redis,
            "ai_service": self.check_ai_service,
            "storage": self.check_storage
        }

    async def check_health(self, detailed: bool = False):
        """Perform health check"""
        results = {}
        overall_status = "healthy"

        for check_name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[check_name] = {"status": "healthy", **result}
            except Exception as e:
                results[check_name] = {"status": "unhealthy", "error": str(e)}
                overall_status = "unhealthy"

        if detailed:
            return {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "checks": results,
                "version": "4.2.0"
            }
        else:
            return {"status": overall_status}

    async def check_database(self):
        """Check database connectivity"""
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            return {"response_time": 0.1}

    async def check_redis(self):
        """Check Redis connectivity"""
        start_time = time.time()
        await redis.ping()
        response_time = time.time() - start_time
        return {"response_time": response_time}

    async def check_ai_service(self):
        """Check AI service availability"""
        models = await model_manager.get_loaded_models()
        return {"models_loaded": len(models)}

    async def check_storage(self):
        """Check storage availability"""
        disk_usage = psutil.disk_usage('/')
        return {
            "total": disk_usage.total,
            "used": disk_usage.used,
            "free": disk_usage.free,
            "percent": disk_usage.percent
        }
```

### 3. Log Management

#### Structured Logging Configuration
```python
import structlog
import logging
from pythonjsonlogger import jsonlogger

class LogConfig:
    @staticmethod
    def setup_logging():
        """Setup structured logging"""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Configure standard logging
        logging.basicConfig(
            format="%(message)s",
            level=logging.INFO,
            handlers=[logging.StreamHandler()]
        )

        # Set up JSON logging for production
        json_handler = logging.StreamHandler()
        json_handler.setFormatter(
            jsonlogger.JsonFormatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s'
            )
        )

        # Add handlers to different loggers
        logger = logging.getLogger()
        logger.addHandler(json_handler)

        return structlog.get_logger()
```

#### Log Analysis
```python
from duckbot.core.log_analyzer import LogAnalyzer

class LogAnalyzer:
    def __init__(self):
        self.error_patterns = [
            r"ERROR\s+.*",
            r"Exception\s+.*",
            r"Traceback.*",
        ]
        self.warning_patterns = [
            r"WARNING\s+.*",
            r"deprecated.*",
            r"slow.*request.*",
        ]

    async def analyze_logs(self, time_range: str = "1h"):
        """Analyze logs for patterns and anomalies"""
        logs = await self._get_logs(time_range)

        analysis = {
            "total_logs": len(logs),
            "error_count": 0,
            "warning_count": 0,
            "error_rate": 0.0,
            "warning_rate": 0.0,
            "top_errors": [],
            "performance_issues": [],
            "security_events": []
        }

        for log in logs:
            # Count errors and warnings
            if any(re.search(pattern, log["message"]) for pattern in self.error_patterns):
                analysis["error_count"] += 1
                analysis["top_errors"].append(log["message"])

            if any(re.search(pattern, log["message"]) for pattern in self.warning_patterns):
                analysis["warning_count"] += 1

            # Check for performance issues
            if "slow" in log["message"].lower() and "request" in log["message"].lower():
                analysis["performance_issues"].append(log)

            # Check for security events
            if any(keyword in log["message"].lower() for keyword in ["unauthorized", "forbidden", "security"]):
                analysis["security_events"].append(log)

        # Calculate rates
        if analysis["total_logs"] > 0:
            analysis["error_rate"] = analysis["error_count"] / analysis["total_logs"]
            analysis["warning_rate"] = analysis["warning_count"] / analysis["total_logs"]

        return analysis

    async def _get_logs(self, time_range: str):
        """Get logs from log storage"""
        # Implementation depends on log storage system
        # This could be Elasticsearch, PostgreSQL, or file-based logs
        pass
```

### 4. Performance Monitoring

#### APM Integration
```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader

class APMIntegration:
    def __init__(self, service_name: str = "duckbot"):
        self.service_name = service_name
        self.setup_tracing()
        self.setup_metrics()

    def setup_tracing(self):
        """Setup distributed tracing"""
        resource = Resource.create({"service.name": self.service_name})

        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)

        # Setup Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=6831,
        )

        tracer_provider.add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )

    def setup_metrics(self):
        """Setup metrics collection"""
        resource = Resource.create({"service.name": self.service_name})

        reader = PrometheusMetricReader()
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(meter_provider)

    def create_span(self, name: str):
        """Create new trace span"""
        tracer = trace.get_tracer(self.service_name)
        return tracer.start_span(name)

    def record_metric(self, name: str, value: float, attributes: dict = None):
        """Record custom metric"""
        meter = metrics.get_meter(self.service_name)
        counter = meter.create_counter(name)
        counter.add(value, attributes or {})
```

## Backup and Recovery

### 1. Database Backup Strategy

#### PostgreSQL Backup Script
```bash
#!/bin/bash
# backup_postgresql.sh

# Configuration
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="duckbot"
DB_USER="duckbot_user"
BACKUP_DIR="/var/backups/postgresql"
RETENTION_DAYS=30
S3_BUCKET="s3://your-backup-bucket/postgresql"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/duckbot_$TIMESTAMP.sql"

# Create backup
echo "Creating PostgreSQL backup..."
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F c -f "$BACKUP_FILE"

# Compress backup
echo "Compressing backup..."
gzip "$BACKUP_FILE"
COMPRESSED_FILE="$BACKUP_FILE.gz"

# Upload to S3
echo "Uploading to S3..."
aws s3 cp "$COMPRESSED_FILE" "$S3_BUCKET/duckbot_$TIMESTAMP.sql.gz"

# Clean old backups
echo "Cleaning old backups..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Log backup status
echo "Backup completed: $COMPRESSED_FILE" >> /var/log/postgresql_backup.log

# Verify backup
echo "Verifying backup..."
if pg_restore -l "$COMPRESSED_FILE" > /dev/null 2>&1; then
    echo "Backup verification successful" >> /var/log/postgresql_backup.log
else
    echo "Backup verification failed" >> /var/log/postgresql_backup.log
    exit 1
fi
```

#### MongoDB Backup Script
```bash
#!/bin/bash
# backup_mongodb.sh

# Configuration
MONGODB_HOST="localhost"
MONGODB_PORT="27017"
MONGODB_DB="duckbot"
BACKUP_DIR="/var/backups/mongodb"
RETENTION_DAYS=30
S3_BUCKET="s3://your-backup-bucket/mongodb"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/mongodb_$TIMESTAMP"

# Create backup
echo "Creating MongoDB backup..."
mongodump --host "$MONGODB_HOST" --port "$MONGODB_PORT" --db "$MONGODB_DB" --out "$BACKUP_PATH"

# Compress backup
echo "Compressing backup..."
tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "mongodb_$TIMESTAMP"

# Upload to S3
echo "Uploading to S3..."
aws s3 cp "$BACKUP_PATH.tar.gz" "$S3_BUCKET/mongodb_$TIMESTAMP.tar.gz"

# Clean old backups
echo "Cleaning old backups..."
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Log backup status
echo "Backup completed: $BACKUP_PATH.tar.gz" >> /var/log/mongodb_backup.log

# Clean up temporary files
rm -rf "$BACKUP_PATH"
```

### 2. Configuration Backup

#### Configuration Backup Script
```bash
#!/bin/bash
# backup_config.sh

# Configuration
CONFIG_DIR="/etc/duckbot"
BACKUP_DIR="/var/backups/config"
RETENTION_DAYS=30
S3_BUCKET="s3://your-backup-bucket/config"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/config_$TIMESTAMP.tar.gz"

# Create backup
echo "Creating configuration backup..."
tar -czf "$BACKUP_FILE" -C "$CONFIG_DIR" .

# Upload to S3
echo "Uploading to S3..."
aws s3 cp "$BACKUP_FILE" "$S3_BUCKET/config_$TIMESTAMP.tar.gz"

# Clean old backups
echo "Cleaning old backups..."
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Log backup status
echo "Backup completed: $BACKUP_FILE" >> /var/log/config_backup.log

# Verify backup
echo "Verifying backup..."
if tar -tzf "$BACKUP_FILE" > /dev/null 2>&1; then
    echo "Backup verification successful" >> /var/log/config_backup.log
else
    echo "Backup verification failed" >> /var/log/config_backup.log
    exit 1
fi
```

### 3. Recovery Procedures

#### Database Recovery
```bash
#!/bin/bash
# restore_postgresql.sh

# Configuration
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="duckbot"
DB_USER="duckbot_user"
BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Drop existing database
echo "Dropping existing database..."
dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"

# Create new database
echo "Creating new database..."
createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"

# Restore backup
echo "Restoring backup..."
pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v "$BACKUP_FILE"

echo "Restore completed successfully"
```

#### Configuration Recovery
```bash
#!/bin/bash
# restore_config.sh

# Configuration
CONFIG_DIR="/etc/duckbot"
BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Create backup of current configuration
echo "Creating backup of current configuration..."
cp -r "$CONFIG_DIR" "$CONFIG_DIR.backup.$(date +%Y%m%d_%H%M%S)"

# Restore configuration
echo "Restoring configuration..."
tar -xzf "$BACKUP_FILE" -C "$CONFIG_DIR"

# Set proper permissions
echo "Setting permissions..."
chown -R duckbot:duckbot "$CONFIG_DIR"
chmod -R 644 "$CONFIG_DIR"
find "$CONFIG_DIR" -type d -exec chmod 755 {} \;

echo "Configuration restore completed successfully"
```

### 4. Disaster Recovery Plan

#### Disaster Recovery Checklist
```markdown
# DuckBot Disaster Recovery Checklist

## Immediate Actions (0-30 minutes)
- [ ] Assess the extent of the damage
- [ ] Notify stakeholders and team members
- [ ] Activate disaster recovery team
- [ ] Switch to backup systems if available
- [ ] Initialize incident response procedures

## System Assessment (30-60 minutes)
- [ ] Identify affected systems and services
- [ ] Determine root cause of the disaster
- [ ] Assess data loss and corruption
- [ ] Estimate recovery time objectives (RTO)
- [ ] Estimate recovery point objectives (RPO)

## Recovery Execution (1-4 hours)
- [ ] Restore database from latest backup
- [ ] Restore configuration files
- [ ] Restart core services
- [ ] Verify system functionality
- [ ] Test critical integrations

## Validation (4-6 hours)
- [ ] Perform end-to-end testing
- [ ] Validate data integrity
- [ ] Check performance metrics
- [ ] Verify security controls
- [ ] Test backup and recovery procedures

## Communication (Throughout)
- [ ] Regular status updates to stakeholders
- [ ] Communication with users about service status
- [ ] Coordination with external vendors and partners
- [ ] Documentation of recovery process

## Post-Recovery (6-24 hours)
- [ ] Conduct post-mortem analysis
- [ ] Update disaster recovery plan
- [ ] Implement preventive measures
- [ ] Schedule follow-up reviews
- [ ] Update documentation
```

## Scaling and High Availability

### 1. Horizontal Scaling

#### Load Balancer Configuration
```nginx
# nginx.conf for multiple backend servers
upstream duckbot_backend {
    least_conn;
    server 10.0.1.10:8787 weight=5;
    server 10.0.1.11:8787 weight=5;
    server 10.0.1.12:8787 weight=5;
    keepalive 32;
}

server {
    listen 80;
    server_name duckbot.example.com;

    location / {
        proxy_pass http://duckbot_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Health check
        proxy_connect_timeout 5s;
        proxy_read_timeout 30s;
        proxy_send_timeout 30s;
    }

    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

#### Database Replication Setup
```sql
-- PostgreSQL replication setup
-- Master server
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 3;
ALTER SYSTEM SET max_replication_slots = 3;
ALTER SYSTEM SET hot_standby = on;

-- Create replication user
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_password';
GRANT REPLICATION TO replicator;

-- Create replication slot
SELECT * FROM pg_create_physical_replication_slot('replication_slot');

-- Add to pg_hba.conf for replica connections
host replication replicator 10.0.1.0/24 md5

-- Reload PostgreSQL
SELECT pg_reload_conf();
```

#### Replica Configuration
```bash
# replica postgresql.conf
wal_level = replica
hot_standby = on
max_standby_streaming_delay = 30s
max_standby_archive_delay = 30s
hot_standby_feedback = on
```

### 2. Auto-scaling Configuration

#### Kubernetes Horizontal Pod Autoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: duckbot-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: duckbot-web
  minReplicas: 3
  maxReplicas: 20
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
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: 100
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Max
```

#### AWS Auto Scaling Group
```python
import boto3

class AWSScalingManager:
    def __init__(self):
        self.autoscaling = boto3.client('autoscaling')
        self.cloudwatch = boto3.client('cloudwatch')

    def create_scaling_policy(self):
        """Create auto-scaling policy"""
        response = self.autoscaling.put_scaling_policy(
            PolicyName='duckbot-cpu-scaling',
            AutoScalingGroupName='duckbot-asg',
            PolicyType='TargetTrackingScaling',
            TargetTrackingConfiguration={
                'PredefinedMetricSpecification': {
                    'PredefinedMetricType': 'ASGAverageCPUUtilization'
                },
                'TargetValue': 70.0,
                'DisableScaleIn': False
            }
        )
        return response

    def setup_cloudwatch_alarms(self):
        """Setup CloudWatch alarms for scaling"""
        alarms = [
            {
                'AlarmName': 'duckbot-high-cpu',
                'MetricName': 'CPUUtilization',
                'Namespace': 'AWS/EC2',
                'Statistic': 'Average',
                'Period': 300,
                'EvaluationPeriods': 2,
                'Threshold': 80.0,
                'ComparisonOperator': 'GreaterThanThreshold',
                'AlarmActions': ['arn:aws:autoscaling:region:account-id:scalingPolicy:policy-id']
            },
            {
                'AlarmName': 'duckbot-high-memory',
                'MetricName': 'MemoryUtilization',
                'Namespace': 'CWAgent',
                'Statistic': 'Average',
                'Period': 300,
                'EvaluationPeriods': 2,
                'Threshold': 85.0,
                'ComparisonOperator': 'GreaterThanThreshold',
                'AlarmActions': ['arn:aws:autoscaling:region:account-id:scalingPolicy:policy-id']
            }
        ]

        for alarm in alarms:
            self.cloudwatch.put_metric_alarm(**alarm)
```

### 3. High Availability Architecture

#### Multi-Region Deployment
```yaml
# Global service configuration
apiVersion: v1
kind: Service
metadata:
  name: duckbot-global
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  selector:
    app: duckbot
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8787
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: duckbot-global-ingress
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/session-cookie-name: "route"
    nginx.ingress.kubernetes.io/session-cookie-expires: "172800"
    nginx.ingress.kubernetes.io/session-cookie-max-age: "172800"
spec:
  tls:
  - hosts:
    - duckbot.example.com
    secretName: duckbot-tls
  rules:
  - host: duckbot.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: duckbot-global
            port:
              number: 80
```

#### Database High Availability
```sql
-- PostgreSQL high availability setup with Patroni
-- Create replication users
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_password';
CREATE USER patroni WITH SUPERUSER ENCRYPTED PASSWORD 'patroni_password';

-- Set up replication slots
SELECT * FROM pg_create_physical_replication_slot('standby_1');
SELECT * FROM pg_create_physical_replication_slot('standby_2');

-- Configure synchronous replication
ALTER SYSTEM SET synchronous_commit = 'on';
ALTER SYSTEM SET synchronous_standby_names = 'standby_1,standby_2';
```

#### Cache High Availability
```redis
# Redis Sentinel configuration
port 26379
sentinel announce-ip <sentinel-ip>
sentinel announce-port 26379
sentinel monitor mymaster <redis-master-ip> 6379 2
sentinel auth-pass mymaster <redis-password>
sentinel down-after-milliseconds mymaster 30000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 180000
sentinel notification-script mymaster /etc/redis/sentinel_notify.sh
sentinel client-reconfig-script mymaster /etc/redis/sentinel_client_reconfig.sh
```

## Troubleshooting

### 1. Common Issues and Solutions

#### Performance Issues
```python
class PerformanceTroubleshooter:
    def __init__(self):
        self.metrics_collector = MetricsCollector()

    async def diagnose_performance_issues(self):
        """Diagnose performance issues"""
        issues = []

        # Check CPU usage
        cpu_usage = await self.metrics_collector.get_cpu_usage()
        if cpu_usage > 80:
            issues.append({
                "type": "high_cpu",
                "severity": "warning",
                "message": f"High CPU usage: {cpu_usage}%",
                "solutions": [
                    "Scale up resources",
                    "Optimize application code",
                    "Check for infinite loops"
                ]
            })

        # Check memory usage
        memory_usage = await self.metrics_collector.get_memory_usage()
        if memory_usage > 85:
            issues.append({
                "type": "high_memory",
                "severity": "critical",
                "message": f"High memory usage: {memory_usage}%",
                "solutions": [
                    "Restart application",
                    "Check for memory leaks",
                    "Increase available memory"
                ]
            })

        # Check response times
        response_time = await self.metrics_collector.get_average_response_time()
        if response_time > 2.0:
            issues.append({
                "type": "slow_response",
                "severity": "warning",
                "message": f"Slow response time: {response_time}s",
                "solutions": [
                    "Optimize database queries",
                    "Implement caching",
                    "Scale horizontally"
                ]
            })

        return issues
```

#### Database Issues
```python
class DatabaseTroubleshooter:
    def __init__(self):
        self.db_manager = DatabaseManager()

    async def diagnose_database_issues(self):
        """Diagnose database issues"""
        issues = []

        # Check connection pool
        pool_status = await self.db_manager.get_connection_pool_status()
        if pool_status["active_connections"] > pool_status["max_connections"] * 0.8:
            issues.append({
                "type": "connection_pool_exhausted",
                "severity": "critical",
                "message": "Database connection pool nearly exhausted",
                "solutions": [
                    "Increase connection pool size",
                    "Implement connection pooling",
                    "Optimize query performance"
                ]
            })

        # Check slow queries
        slow_queries = await self.db_manager.get_slow_queries()
        if slow_queries:
            issues.append({
                "type": "slow_queries",
                "severity": "warning",
                "message": f"Found {len(slow_queries)} slow queries",
                "solutions": [
                    "Optimize query execution plans",
                    "Add missing indexes",
                    "Implement query caching"
                ]
            })

        # Check database size
        db_size = await self.db_manager.get_database_size()
        if db_size > 100 * 1024 * 1024 * 1024:  # 100GB
            issues.append({
                "type": "large_database",
                "severity": "warning",
                "message": f"Large database size: {db_size / (1024**3):.2f}GB",
                "solutions": [
                    "Implement data archiving",
                    "Optimize storage",
                    "Consider sharding"
                ]
            })

        return issues
```

#### AI Service Issues
```python
class AIServiceTroubleshooter:
    def __init__(self):
        self.ai_manager = AIManager()

    async def diagnose_ai_service_issues(self):
        """Diagnose AI service issues"""
        issues = []

        # Check model availability
        models = await self.ai_manager.get_available_models()
        unavailable_models = [m for m in models if not m["loaded"]]
        if unavailable_models:
            issues.append({
                "type": "models_not_loaded",
                "severity": "warning",
                "message": f"Models not loaded: {', '.join(unavailable_models)}",
                "solutions": [
                    "Check system resources",
                    "Restart AI service",
                    "Load models manually"
                ]
            })

        # Check API rate limits
        rate_limits = await self.ai_manager.get_rate_limit_status()
        if rate_limits["remaining"] < rate_limits["limit"] * 0.1:
            issues.append({
                "type": "rate_limit_exceeded",
                "severity": "critical",
                "message": "API rate limit nearly exceeded",
                "solutions": [
                    "Wait for rate limit reset",
                    "Implement request queuing",
                    "Upgrade API plan"
                ]
            })

        # Check response quality
        response_quality = await self.ai_manager.get_response_quality_metrics()
        if response_quality["error_rate"] > 0.05:
            issues.append({
                "type": "high_error_rate",
                "severity": "critical",
                "message": f"High error rate: {response_quality['error_rate']*100:.2f}%",
                "solutions": [
                    "Check AI service status",
                    "Verify API credentials",
                    "Implement retry logic"
                ]
            })

        return issues
```

### 2. Debugging Tools

#### System Diagnostic Script
```python
#!/usr/bin/env python3
# system_diagnostic.py

import psutil
import asyncio
import aiohttp
import asyncpg
from datetime import datetime

class SystemDiagnostic:
    def __init__(self):
        self.results = {}

    async def run_diagnostics(self):
        """Run complete system diagnostic"""
        print("Starting system diagnostic...")

        await self.check_system_resources()
        await self.check_database_connectivity()
        await self.check_redis_connectivity()
        await self.check_ai_service()
        await self.check_web_service()

        self.generate_report()

    async def check_system_resources(self):
        """Check system resources"""
        print("Checking system resources...")

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        # Memory usage
        memory = psutil.virtual_memory()

        # Disk usage
        disk = psutil.disk_usage('/')

        # Network interfaces
        network = psutil.net_io_counters()

        self.results["system_resources"] = {
            "cpu": {
                "usage_percent": cpu_percent,
                "count": cpu_count
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        }

        print(f"CPU Usage: {cpu_percent}%")
        print(f"Memory Usage: {memory.percent}%")
        print(f"Disk Usage: {disk.percent}%")

    async def check_database_connectivity(self):
        """Check database connectivity"""
        print("Checking database connectivity...")

        try:
            conn = await asyncpg.connect(
                "postgresql://user:password@localhost:5432/duckbot"
            )

            # Test query
            result = await conn.fetchval("SELECT 1")

            await conn.close()

            self.results["database"] = {
                "status": "healthy",
                "response_time": 0.1,  # This would be measured
                "error": None
            }

            print("Database: Healthy")

        except Exception as e:
            self.results["database"] = {
                "status": "unhealthy",
                "response_time": None,
                "error": str(e)
            }

            print(f"Database: Unhealthy - {e}")

    async def check_redis_connectivity(self):
        """Check Redis connectivity"""
        print("Checking Redis connectivity...")

        try:
            import redis.asyncio as redis

            redis_client = redis.Redis(host='localhost', port=6379)

            # Test connection
            response_time = await redis_client.ping()

            self.results["redis"] = {
                "status": "healthy",
                "response_time": 0.05,  # This would be measured
                "error": None
            }

            print("Redis: Healthy")

        except Exception as e:
            self.results["redis"] = {
                "status": "unhealthy",
                "response_time": None,
                "error": str(e)
            }

            print(f"Redis: Unhealthy - {e}")

    async def check_ai_service(self):
        """Check AI service"""
        print("Checking AI service...")

        try:
            # Test AI service endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8787/api/v1/models") as response:
                    if response.status == 200:
                        self.results["ai_service"] = {
                            "status": "healthy",
                            "response_time": 0.2,  # This would be measured
                            "error": None
                        }
                        print("AI Service: Healthy")
                    else:
                        raise Exception(f"HTTP {response.status}")

        except Exception as e:
            self.results["ai_service"] = {
                "status": "unhealthy",
                "response_time": None,
                "error": str(e)
            }

            print(f"AI Service: Unhealthy - {e}")

    async def check_web_service(self):
        """Check web service"""
        print("Checking web service...")

        try:
            # Test web service endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8787/api/v1/health") as response:
                    if response.status == 200:
                        self.results["web_service"] = {
                            "status": "healthy",
                            "response_time": 0.1,  # This would be measured
                            "error": None
                        }
                        print("Web Service: Healthy")
                    else:
                        raise Exception(f"HTTP {response.status}")

        except Exception as e:
            self.results["web_service"] = {
                "status": "unhealthy",
                "response_time": None,
                "error": str(e)
            }

            print(f"Web Service: Unhealthy - {e}")

    def generate_report(self):
        """Generate diagnostic report"""
        print("\n" + "="*50)
        print("SYSTEM DIAGNOSTIC REPORT")
        print("="*50)
        print(f"Generated at: {datetime.now().isoformat()}")
        print()

        # System Resources
        print("SYSTEM RESOURCES:")
        print(f"  CPU Usage: {self.results['system_resources']['cpu']['usage_percent']}%")
        print(f"  Memory Usage: {self.results['system_resources']['memory']['percent']}%")
        print(f"  Disk Usage: {self.results['system_resources']['disk']['percent']}%")
        print()

        # Services Status
        print("SERVICES STATUS:")
        for service in ["database", "redis", "ai_service", "web_service"]:
            status = self.results[service]["status"]
            print(f"  {service.replace('_', ' ').title()}: {status.upper()}")
            if self.results[service]["error"]:
                print(f"    Error: {self.results[service]['error']}")
        print()

        # Overall Health
        all_healthy = all(
            self.results[service]["status"] == "healthy"
            for service in ["database", "redis", "ai_service", "web_service"]
        )

        print("OVERALL HEALTH:", "HEALTHY" if all_healthy else "UNHEALTHY")
        print("="*50)

if __name__ == "__main__":
    diagnostic = SystemDiagnostic()
    asyncio.run(diagnostic.run_diagnostics())
```

### 3. Log Analysis Tools

#### Log Analysis Script
```python
#!/usr/bin/env python3
# log_analyzer.py

import re
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import pandas as pd

class LogAnalyzer:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.logs = []
        self.error_patterns = [
            r"ERROR\s+.*",
            r"Exception\s+.*",
            r"Traceback.*",
            r"Failed.*",
            r"Timeout.*"
        ]
        self.warning_patterns = [
            r"WARNING\s+.*",
            r"deprecated.*",
            r"slow.*request.*",
            r"retry.*"
        ]

    def parse_logs(self):
        """Parse log file"""
        print(f"Parsing logs from {self.log_file_path}...")

        with open(self.log_file_path, 'r') as f:
            for line in f:
                try:
                    # Try to parse as JSON first
                    log_entry = json.loads(line.strip())
                    self.logs.append(log_entry)
                except json.JSONDecodeError:
                    # Parse as plain text
                    log_entry = self.parse_plain_log(line.strip())
                    if log_entry:
                        self.logs.append(log_entry)

        print(f"Parsed {len(self.logs)} log entries")

    def parse_plain_log(self, line):
        """Parse plain text log entry"""
        # Common log format parsing
        patterns = [
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) (.*)',
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) (\w+) (.*)',
        ]

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                return {
                    "timestamp": match.group(1),
                    "level": match.group(2),
                    "message": match.group(3),
                    "raw": line
                }

        return {"raw": line}

    def analyze_error_patterns(self):
        """Analyze error patterns"""
        print("Analyzing error patterns...")

        errors = []
        warnings = []

        for log in self.logs:
            message = log.get("message", log.get("raw", ""))

            # Check for errors
            if any(re.search(pattern, message, re.IGNORECASE) for pattern in self.error_patterns):
                errors.append(log)

            # Check for warnings
            if any(re.search(pattern, message, re.IGNORECASE) for pattern in self.warning_patterns):
                warnings.append(log)

        return {
            "total_errors": len(errors),
            "total_warnings": len(warnings),
            "error_rate": len(errors) / len(self.logs) if self.logs else 0,
            "warning_rate": len(warnings) / len(self.logs) if self.logs else 0,
            "recent_errors": [e for e in errors[-10:]],  # Last 10 errors
            "top_error_messages": Counter([e.get("message", "") for e in errors]).most_common(5)
        }

    def analyze_performance(self):
        """Analyze performance metrics"""
        print("Analyzing performance metrics...")

        # Extract performance-related logs
        performance_logs = []
        for log in self.logs:
            message = log.get("message", "")
            if any(keyword in message.lower() for keyword in ["slow", "timeout", "latency", "response_time"]):
                performance_logs.append(log)

        # Extract response times
        response_times = []
        for log in performance_logs:
            message = log.get("message", "")
            # Look for response time patterns
            response_time_match = re.search(r'response[_\s]?time[:\s]*(\d+\.?\d*)', message)
            if response_time_match:
                response_times.append(float(response_time_match.group(1)))

        return {
            "total_performance_issues": len(performance_logs),
            "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "slow_requests": len([t for t in response_times if t > 1.0]),  # Requests > 1s
            "performance_logs": performance_logs[-10:]  # Last 10 performance logs
        }

    def analyze_security_events(self):
        """Analyze security-related events"""
        print("Analyzing security events...")

        security_events = []
        security_keywords = ["unauthorized", "forbidden", "authentication", "permission", "security", "breach"]

        for log in self.logs:
            message = log.get("message", "")
            if any(keyword in message.lower() for keyword in security_keywords):
                security_events.append(log)

        return {
            "total_security_events": len(security_events),
            "recent_security_events": security_events[-10:],  # Last 10 security events
            "security_event_types": Counter([
                next((kw for kw in security_keywords if kw in message.lower()), "other")
                for event in security_events
                for message in [event.get("message", "")]
            ])
        }

    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("Generating analysis report...")

        # Parse logs if not already parsed
        if not self.logs:
            self.parse_logs()

        # Perform analysis
        error_analysis = self.analyze_error_patterns()
        performance_analysis = self.analyze_performance()
        security_analysis = self.analyze_security_events()

        # Generate report
        report = {
            "analysis_time": datetime.now().isoformat(),
            "log_file": self.log_file_path,
            "total_logs": len(self.logs),
            "time_range": {
                "start": self.logs[0].get("timestamp") if self.logs else None,
                "end": self.logs[-1].get("timestamp") if self.logs else None
            },
            "error_analysis": error_analysis,
            "performance_analysis": performance_analysis,
            "security_analysis": security_analysis,
            "recommendations": self.generate_recommendations(
                error_analysis, performance_analysis, security_analysis
            )
        }

        # Save report
        report_file = f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Report saved to {report_file}")

        # Print summary
        self.print_summary(report)

        return report

    def generate_recommendations(self, error_analysis, performance_analysis, security_analysis):
        """Generate recommendations based on analysis"""
        recommendations = []

        # Error-based recommendations
        if error_analysis["error_rate"] > 0.05:
            recommendations.append({
                "priority": "high",
                "category": "error_reduction",
                "message": "High error rate detected. Implement better error handling and logging."
            })

        # Performance-based recommendations
        if performance_analysis["average_response_time"] > 1.0:
            recommendations.append({
                "priority": "medium",
                "category": "performance",
                "message": "Slow response times detected. Optimize database queries and implement caching."
            })

        # Security-based recommendations
        if security_analysis["total_security_events"] > 0:
            recommendations.append({
                "priority": "high",
                "category": "security",
                "message": "Security events detected. Review authentication and authorization mechanisms."
            })

        return recommendations

    def print_summary(self, report):
        """Print analysis summary"""
        print("\n" + "="*60)
        print("LOG ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total Logs Analyzed: {report['total_logs']}")
        print(f"Error Rate: {report['error_analysis']['error_rate']*100:.2f}%")
        print(f"Warning Rate: {report['error_analysis']['warning_rate']*100:.2f}%")
        print(f"Average Response Time: {report['performance_analysis']['average_response_time']:.2f}s")
        print(f"Security Events: {report['security_analysis']['total_security_events']}")
        print("\nTOP RECOMMENDATIONS:")
        for rec in report["recommendations"][:3]:
            print(f"  [{rec['priority'].upper()}] {rec['message']}")
        print("="*60)

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python log_analyzer.py <log_file_path>")
        sys.exit(1)

    log_file_path = sys.argv[1]
    analyzer = LogAnalyzer(log_file_path)
    analyzer.generate_report()
```

## Best Practices

### 1. Security Best Practices

#### Regular Security Audits
```python
class SecurityAuditor:
    def __init__(self):
        self.audit_checks = [
            self.check_password_policy,
            self.check_api_key_rotation,
            self.check_ssl_certificates,
            self.check_access_controls,
            self.check_data_encryption
        ]

    async def conduct_security_audit(self):
        """Conduct comprehensive security audit"""
        audit_results = {}

        for check in self.audit_checks:
            check_name = check.__name__
            try:
                result = await check()
                audit_results[check_name] = result
            except Exception as e:
                audit_results[check_name] = {
                    "status": "error",
                    "message": f"Audit check failed: {str(e)}"
                }

        return audit_results

    async def check_password_policy(self):
        """Check password policy compliance"""
        # Check password requirements
        min_length = 12
        require_special_chars = True
        require_numbers = True
        require_uppercase = True

        # Check user passwords
        users = await self.get_all_users()
        non_compliant_users = []

        for user in users:
            password = user.get("password", "")
            if len(password) < min_length:
                non_compliant_users.append(user["username"])
            if require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                non_compliant_users.append(user["username"])
            if require_numbers and not re.search(r'\d', password):
                non_compliant_users.append(user["username"])
            if require_uppercase and not re.search(r'[A-Z]', password):
                non_compliant_users.append(user["username"])

        return {
            "status": "compliant" if not non_compliant_users else "non_compliant",
            "non_compliant_users": non_compliant_users,
            "recommendations": [
                "Enforce stronger password requirements",
                "Implement password expiration policy",
                "Enable multi-factor authentication"
            ]
        }
```

#### Access Control Best Practices
```python
class AccessControlManager:
    def __init__(self):
        self.role_permissions = {
            "admin": ["read", "write", "delete", "manage_users", "manage_system"],
            "user": ["read", "write"],
            "guest": ["read"]
        }

    def check_permission(self, user_role, required_permission):
        """Check if user has required permission"""
        user_permissions = self.role_permissions.get(user_role, [])
        return required_permission in user_permissions

    def enforce_access_control(self, user, resource, action):
        """Enforce access control policies"""
        # Check user role
        user_role = user.get("role", "guest")

        # Check resource-specific permissions
        resource_permissions = self.get_resource_permissions(resource)

        # Check if user has required permission
        if not self.check_permission(user_role, action):
            raise PermissionError(f"User {user['username']} does not have permission to {action} on {resource}")

        # Additional checks for sensitive operations
        if action in ["delete", "manage_users", "manage_system"]:
            if not self.verify_mfa(user):
                raise PermissionError("Multi-factor authentication required for this operation")

        return True
```

### 2. Performance Best Practices

#### Caching Strategy
```python
class CacheManager:
    def __init__(self):
        self.cache = {}
        self.ttls = {}
        self.access_counts = {}

    def get(self, key):
        """Get value from cache with performance tracking"""
        if key in self.cache:
            # Update access count
            self.access_counts[key] = self.access_counts.get(key, 0) + 1

            # Check TTL
            if self.ttls.get(key, float('inf')) > time.time():
                return self.cache[key]
            else:
                # Remove expired item
                self.remove(key)

        return None

    def set(self, key, value, ttl=3600):
        """Set value in cache with TTL"""
        self.cache[key] = value
        self.ttls[key] = time.time() + ttl
        self.access_counts[key] = 0

    def remove(self, key):
        """Remove item from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.ttls:
            del self.ttls[key]
        if key in self.access_counts:
            del self.access_counts[key]

    def cleanup_expired(self):
        """Remove expired items from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, ttl in self.ttls.items()
            if ttl <= current_time
        ]

        for key in expired_keys:
            self.remove(key)

        return len(expired_keys)

    def get_cache_stats(self):
        """Get cache performance statistics"""
        total_accesses = sum(self.access_counts.values())
        hit_rate = total_accesses / len(self.access_counts) if self.access_counts else 0

        return {
            "total_items": len(self.cache),
            "total_accesses": total_accesses,
            "hit_rate": hit_rate,
            "memory_usage": sum(len(str(v)) for v in self.cache.values())
        }
```

#### Database Optimization
```python
class DatabaseOptimizer:
    def __init__(self, engine):
        self.engine = engine

    async def analyze_query_performance(self, query, params=None):
        """Analyze query performance"""
        async with self.engine.begin() as conn:
            # Enable query timing
            await conn.execute("SET log_statement = 'all'")
            await conn.execute("SET log_min_duration_statement = 0")

            # Execute query
            start_time = time.time()
            result = await conn.execute(query, params or {})
            execution_time = time.time() - start_time

            # Get query plan
            plan_result = await conn.execute(f"EXPLAIN ANALYZE {query}", params or {})
            plan = plan_result.fetchall()

            return {
                "execution_time": execution_time,
                "rows_returned": len(result.fetchall()),
                "query_plan": plan,
                "recommendations": self.generate_query_recommendations(plan, execution_time)
            }

    def generate_query_recommendations(self, plan, execution_time):
        """Generate query optimization recommendations"""
        recommendations = []

        # Check for sequential scans
        if "Seq Scan" in str(plan):
            recommendations.append("Consider adding indexes for frequently accessed columns")

        # Check for slow execution
        if execution_time > 1.0:
            recommendations.append("Query execution time is slow. Consider optimizing the query or adding indexes")

        # Check for high cost
        if "cost=" in str(plan):
            cost_match = re.search(r"cost=(\d+\.\d+)\.\.(\d+\.\d+)", str(plan))
            if cost_match and float(cost_match.group(2)) > 10000:
                recommendations.append("Query has high cost. Consider query optimization or materialized views")

        return recommendations
```

### 3. Monitoring Best Practices

#### Alert Configuration
```python
class AlertManager:
    def __init__(self):
        self.alert_rules = {
            "high_cpu": {
                "condition": lambda metrics: metrics["cpu_usage"] > 80,
                "severity": "warning",
                "message": "High CPU usage detected",
                "actions": ["log", "email", "slack"]
            },
            "high_memory": {
                "condition": lambda metrics: metrics["memory_usage"] > 85,
                "severity": "critical",
                "message": "High memory usage detected",
                "actions": ["log", "email", "slack", "pagerduty"]
            },
            "service_down": {
                "condition": lambda metrics: not metrics["services"]["all_healthy"],
                "severity": "critical",
                "message": "Service health check failed",
                "actions": ["log", "email", "slack", "pagerduty"]
            }
        }

    async def check_alerts(self, metrics):
        """Check alert conditions and trigger alerts"""
        triggered_alerts = []

        for rule_name, rule_config in self.alert_rules.items():
            if rule_config["condition"](metrics):
                alert = {
                    "rule": rule_name,
                    "severity": rule_config["severity"],
                    "message": rule_config["message"],
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics
                }

                # Trigger alert actions
                for action in rule_config["actions"]:
                    await self.trigger_alert_action(alert, action)

                triggered_alerts.append(alert)

        return triggered_alerts

    async def trigger_alert_action(self, alert, action):
        """Trigger specific alert action"""
        if action == "log":
            await self.log_alert(alert)
        elif action == "email":
            await self.send_email_alert(alert)
        elif action == "slack":
            await self.send_slack_alert(alert)
        elif action == "pagerduty":
            await self.send_pagerduty_alert(alert)
```

#### Health Check Implementation
```python
class HealthChecker:
    def __init__(self):
        self.health_checks = {
            "database": self.check_database_health,
            "redis": self.check_redis_health,
            "ai_service": self.check_ai_service_health,
            "web_service": self.check_web_service_health,
            "disk_space": self.check_disk_space_health,
            "memory": self.check_memory_health
        }

    async def run_health_checks(self):
        """Run all health checks"""
        results = {}
        overall_healthy = True

        for check_name, check_func in self.health_checks.items():
            try:
                result = await check_func()
                results[check_name] = result

                if result["status"] != "healthy":
                    overall_healthy = False

            except Exception as e:
                results[check_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
                overall_healthy = False

        return {
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "checks": results,
            "timestamp": datetime.now().isoformat()
        }

    async def check_database_health(self):
        """Check database health"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return {
                    "status": "healthy",
                    "response_time": 0.1,  # Would be measured
                    "last_check": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }

    async def check_disk_space_health(self):
        """Check disk space health"""
        disk_usage = psutil.disk_usage('/')
        free_percent = (disk_usage.free / disk_usage.total) * 100

        status = "healthy"
        if free_percent < 10:
            status = "critical"
        elif free_percent < 20:
            status = "warning"

        return {
            "status": status,
            "free_space_percent": free_percent,
            "total_space_gb": disk_usage.total / (1024**3),
            "free_space_gb": disk_usage.free / (1024**3),
            "last_check": datetime.now().isoformat()
        }
```

This comprehensive administrator guide provides detailed information for deploying, managing, and maintaining DuckBot v4.2 in production environments, covering deployment strategies, performance optimization, security configuration, monitoring, backup procedures, and best practices.