# LHCMS Deployment and Operations Guide

## Production Deployment Architecture

### Infrastructure Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                        Production Environment                   │
├─────────────────────────────────────────────────────────────────┤
│  Load Balancer (ALB/NGINX)                                      │
│  ├─ SSL Termination (TLS 1.3)                                   │
│  ├─ Rate Limiting                                               │
│  └─ Health Checks                                               │
├─────────────────────────────────────────────────────────────────┤
│  Application Tier (Auto Scaling Group)                          │
│  ├─ LHCMS Instance 1 (Docker Container)                         │
│  ├─ LHCMS Instance 2 (Docker Container)                         │
│  └─ LHCMS Instance N (Docker Container)                         │
├─────────────────────────────────────────────────────────────────┤
│  Cache Layer                                                    │
│  ├─ Redis Cluster (Sessions, Cache)                             │
│  └─ ElastiCache (Multi-AZ)                                      │
├─────────────────────────────────────────────────────────────────┤
│  Database Layer                                                 │
│  ├─ PostgreSQL Primary (RDS)                                    │
│  ├─ PostgreSQL Read Replica                                     │
│  └─ Automated Backups (Point-in-Time Recovery)                  │
├─────────────────────────────────────────────────────────────────┤
│  Monitoring & Logging                                           │
│  ├─ CloudWatch/Prometheus                                       │
│  ├─ ELK Stack (Elasticsearch, Logstash, Kibana)                 │
│  └─ APM (New Relic/DataDog)                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Container Configuration

#### Dockerfile (Production)
```dockerfile
# Multi-stage build for production optimization
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r lhcms && useradd -r -g lhcms lhcms

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Set ownership and permissions
RUN chown -R lhcms:lhcms /app
USER lhcms

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Expose port
EXPOSE 5001

# Production command
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "50", "--timeout", "30", "--keep-alive", "2", "--log-level", "info", "app:app"]
```

#### Docker Compose (Development/Testing)
```yaml
version: '3.8'

services:
  lhcms:
    build: .
    ports:
      - "5001:5001"
    environment:
      - FLASK_ENV=development
      - DATABASE_URL=postgresql://lhcms:password@db:5432/lhcms_dev
      - REDIS_URL=redis://redis:6379/0
      - UMS_BASE_URL=http://ums:5000
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - lhcms-network

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: lhcms_dev
      POSTGRES_USER: lhcms
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - lhcms-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - lhcms-network

  ums:
    image: lhcms/ums:latest
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://lhcms:password@db:5432/ums_dev
    depends_on:
      - db
    networks:
      - lhcms-network

volumes:
  postgres_data:
  redis_data:

networks:
  lhcms-network:
    driver: bridge
```

### Kubernetes Deployment

#### Deployment Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lhcms
  labels:
    app: lhcms
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lhcms
  template:
    metadata:
      labels:
        app: lhcms
    spec:
      containers:
      - name: lhcms
        image: lhcms/lhcms:latest
        ports:
        - containerPort: 5001
        env:
        - name: FLASK_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: lhcms-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: lhcms-secrets
              key: secret-key
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
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
            port: 5001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5001
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: lhcms-service
spec:
  selector:
    app: lhcms
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5001
  type: LoadBalancer
```

## Database Configuration

### PostgreSQL Production Setup
```sql
-- Database initialization script
CREATE DATABASE lhcms_prod;
CREATE USER lhcms_app WITH ENCRYPTED PASSWORD 'secure_password';

-- Grant permissions
GRANT CONNECT ON DATABASE lhcms_prod TO lhcms_app;
GRANT USAGE ON SCHEMA public TO lhcms_app;
GRANT CREATE ON SCHEMA public TO lhcms_app;

-- Performance settings
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Security settings
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_checkpoints = on;
```

### Database Migration Strategy
```python
# migrations/env.py
from flask import current_app
from alembic import context
from sqlalchemy import engine_from_config, pool

def run_migrations_online():
    """Run migrations in 'online' mode with connection pooling"""
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = current_app.config.get('DATABASE_URL')
    
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True
        )
        
        with context.begin_transaction():
            context.run_migrations()

# Database migration commands
flask db init       # Initialize migration repository
flask db migrate -m "Add case model"  # Create migration
flask db upgrade    # Apply migrations
flask db downgrade  # Rollback migrations
```

## Security Configuration

### SSL/TLS Configuration
```nginx
# NGINX SSL configuration
server {
    listen 443 ssl http2;
    server_name lhcms.yourdomain.com;
    
    # SSL certificates
    ssl_certificate /etc/ssl/certs/lhcms.crt;
    ssl_certificate_key /etc/ssl/private/lhcms.key;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;" always;
    
    location / {
        proxy_pass http://lhcms-backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

upstream lhcms-backend {
    server 10.0.1.10:5001;
    server 10.0.1.11:5001;
    server 10.0.1.12:5001;
}
```

### Environment Configuration
```bash
# production.env
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key-256-bits
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://host:port/db

# Security settings
BCRYPT_LOG_ROUNDS=15
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=604800
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true

# HIPAA compliance
HIPAA_AUDIT_ENABLED=true
ENCRYPTION_KEY_ID=aws-kms-key-id
DATA_RETENTION_DAYS=2555  # 7 years

# Monitoring
SENTRY_DSN=your-sentry-dsn
NEW_RELIC_LICENSE_KEY=your-new-relic-key

# External services
UMS_BASE_URL=https://ums.yourdomain.com
UMS_API_KEY=secure-api-key
```

## Monitoring and Alerting

### Application Monitoring
```python
# monitoring.py
import time
from functools import wraps
from flask import request, g
from prometheus_client import Counter, Histogram, generate_latest

# Metrics collection
REQUEST_COUNT = Counter('lhcms_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('lhcms_request_duration_seconds', 'Request duration')
CASE_OPERATIONS = Counter('lhcms_case_operations_total', 'Case operations', ['operation', 'status'])

def monitor_requests():
    """Monitor all requests for metrics"""
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        duration = time.time() - g.start_time
        REQUEST_DURATION.observe(duration)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            status=response.status_code
        ).inc()
        return response

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}
```

### Health Check Implementation
```python
@app.route('/health')
def health_check():
    """Comprehensive health check"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': app.config.get('VERSION', '1.0.0'),
        'checks': {}
    }
    
    try:
        # Database connectivity
        db.session.execute('SELECT 1')
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    try:
        # Redis connectivity
        redis_client.ping()
        health_status['checks']['redis'] = 'healthy'
    except Exception as e:
        health_status['checks']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    try:
        # UMS connectivity
        ums_response = requests.get(f"{UMS_BASE_URL}/health", timeout=5)
        if ums_response.status_code == 200:
            health_status['checks']['ums'] = 'healthy'
        else:
            health_status['checks']['ums'] = f'unhealthy: status {ums_response.status_code}'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['ums'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code
```

### Logging Configuration
```python
# logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': '/app/logs/lhcms.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'audit': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filename': '/app/logs/audit.log',
            'maxBytes': 10485760,
            'backupCount': 10
        }
    },
    'loggers': {
        'lhcms': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'audit': {
            'level': 'INFO',
            'handlers': ['audit'],
            'propagate': False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

## Backup and Recovery

### Database Backup Strategy
```bash
#!/bin/bash
# backup_database.sh

# Configuration
DB_HOST="your-db-host"
DB_PORT="5432"
DB_NAME="lhcms_prod"
DB_USER="backup_user"
BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Full database backup
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --format=custom --compress=9 \
    --file="$BACKUP_DIR/lhcms_full_$DATE.backup"

# Verify backup
pg_restore --list "$BACKUP_DIR/lhcms_full_$DATE.backup" > /dev/null
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: lhcms_full_$DATE.backup"
else
    echo "Backup verification failed!"
    exit 1
fi

# Upload to cloud storage (AWS S3)
aws s3 cp "$BACKUP_DIR/lhcms_full_$DATE.backup" \
    s3://your-backup-bucket/postgresql/lhcms/ \
    --storage-class STANDARD_IA

# Clean up old backups
find $BACKUP_DIR -name "lhcms_full_*.backup" -mtime +$RETENTION_DAYS -delete

# Log backup completion
logger "LHCMS database backup completed: lhcms_full_$DATE.backup"
```

### Disaster Recovery Procedures
```bash
#!/bin/bash
# restore_database.sh

# Configuration
BACKUP_FILE="$1"
DB_HOST="your-db-host"
DB_PORT="5432"
DB_NAME="lhcms_prod"
DB_USER="postgres"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Create database if it doesn't exist
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;"

# Restore database
pg_restore -h $DB_HOST -p $DB_PORT -U $DB_USER \
    --dbname=$DB_NAME --clean --if-exists \
    --verbose "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Database restore completed successfully"
else
    echo "Database restore failed!"
    exit 1
fi
```

## Performance Tuning

### Application Optimization
```python
# performance.py
from flask_caching import Cache
from werkzeug.middleware.profiler import ProfilerMiddleware

# Enable caching
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': REDIS_URL,
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Database connection pooling
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 30
}

# Request optimization
@app.before_request
def before_request():
    """Optimize database connections per request"""
    db.session.begin()

@app.teardown_appcontext
def close_db(error):
    """Clean up database connections"""
    db.session.remove()

# Enable profiling in development
if app.config['FLASK_ENV'] == 'development':
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app)
```

### Query Optimization
```python
# Efficient pagination with cursor-based pagination
def get_cases_cursor_paginated(lab_ids, cursor=None, limit=50):
    query = Case.query.filter(Case.lab_id.in_(lab_ids))
    
    if cursor:
        query = query.filter(Case.id > cursor)
    
    cases = query.order_by(Case.id).limit(limit + 1).all()
    
    has_next = len(cases) > limit
    if has_next:
        cases = cases[:-1]
    
    next_cursor = cases[-1].id if cases and has_next else None
    
    return {
        'cases': cases,
        'has_next': has_next,
        'next_cursor': next_cursor
    }

# Bulk operations for better performance
def bulk_update_case_status(case_ids, new_status):
    """Efficiently update multiple cases"""
    db.session.query(Case).filter(
        Case.id.in_(case_ids)
    ).update(
        {Case.status: new_status, Case.updated_at: datetime.utcnow()},
        synchronize_session=False
    )
    db.session.commit()
```

## Deployment Scripts

### Automated Deployment Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: pytest --cov=app tests/
    
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build Docker image
      run: |
        docker build -t lhcms/lhcms:${{ github.sha }} .
        docker tag lhcms/lhcms:${{ github.sha }} lhcms/lhcms:latest
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push lhcms/lhcms:${{ github.sha }}
        docker push lhcms/lhcms:latest
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to production
      run: |
        # Deploy to Kubernetes or your deployment platform
        kubectl set image deployment/lhcms lhcms=lhcms/lhcms:${{ github.sha }}
        kubectl rollout status deployment/lhcms
```

### Zero-Downtime Deployment
```bash
#!/bin/bash
# deploy.sh - Blue-Green deployment script

NEW_VERSION="$1"
CURRENT_VERSION=$(kubectl get deployment lhcms -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d: -f2)

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <new_version>"
    exit 1
fi

echo "Deploying LHCMS version: $NEW_VERSION"
echo "Current version: $CURRENT_VERSION"

# Update deployment
kubectl set image deployment/lhcms lhcms=lhcms/lhcms:$NEW_VERSION

# Wait for rollout to complete
kubectl rollout status deployment/lhcms --timeout=300s

# Health check
sleep 30
HEALTH_CHECK=$(kubectl exec -it $(kubectl get pods -l app=lhcms -o jsonpath='{.items[0].metadata.name}') -- curl -s http://localhost:5001/health | jq -r .status)

if [ "$HEALTH_CHECK" == "healthy" ]; then
    echo "Deployment successful! Version $NEW_VERSION is healthy."
else
    echo "Deployment failed! Rolling back to version $CURRENT_VERSION"
    kubectl set image deployment/lhcms lhcms=lhcms/lhcms:$CURRENT_VERSION
    kubectl rollout status deployment/lhcms
    exit 1
fi
```

This comprehensive deployment and operations guide provides everything needed to deploy LHCMS in a production environment with proper security, monitoring, and reliability measures.
