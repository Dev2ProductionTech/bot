# Phase 6 — Deployment, Monitoring & Documentation

## Task 46: Docker Compose & Kubernetes Manifests

### Development: docker-compose.yml (Enhanced)
```yaml
version: '3.9'

services:
  postgres:
    image: postgres:16-alpine
    container_name: dev2prod_postgres
    environment:
      POSTGRES_USER: botuser
      POSTGRES_PASSWORD: botpass
      POSTGRES_DB: dev2prod_bot
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U botuser"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - bot_network

  redis:
    image: redis:7-alpine
    container_name: dev2prod_redis
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - bot_network

  bot-api:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: dev2prod_bot_api
    environment:
      ENVIRONMENT: development
      DATABASE_URL: postgresql+asyncpg://botuser:botpass@postgres:5432/dev2prod_bot
      REDIS_URL: redis://redis:6379/0
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
      TELEGRAM_WEBHOOK_SECRET: ${TELEGRAM_WEBHOOK_SECRET}
      TELEGRAM_WEBHOOK_URL: ${TELEGRAM_WEBHOOK_URL}
      AGENT_GROUP_CHAT_ID: ${AGENT_GROUP_CHAT_ID}
      LONGCAT_API_KEY: ${LONGCAT_API_KEY}
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./attachments:/app/attachments
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - bot_network

  llm-worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    container_name: dev2prod_llm_worker
    environment:
      ENVIRONMENT: development
      DATABASE_URL: postgresql+asyncpg://botuser:botpass@postgres:5432/dev2prod_bot
      REDIS_URL: redis://redis:6379/0
      LONGCAT_API_KEY: ${LONGCAT_API_KEY}
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2
    networks:
      - bot_network

  prometheus:
    image: prom/prometheus:latest
    container_name: dev2prod_prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - bot_network

  grafana:
    image: grafana/grafana:latest
    container_name: dev2prod_grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_USERS_ALLOW_SIGN_UP: false
    ports:
      - "3000:3000"
    volumes:
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - bot_network

  nginx:
    image: nginx:alpine
    container_name: dev2prod_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - bot-api
    networks:
      - bot_network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  bot_network:
    driver: bridge
```

### Production: Kubernetes Manifests

#### k8s/namespace.yaml
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev2prod-bot
  labels:
    name: dev2prod-bot
    environment: production
```

#### k8s/configmap.yaml
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: bot-config
  namespace: dev2prod-bot
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  LONGCAT_BASE_URL: "https://api.longcat.chat/v1"
  LONGCAT_MODEL: "gpt-4o-mini"
  LONGCAT_MAX_TOKENS: "500"
  MAX_FILE_SIZE_MB: "10"
  RATE_LIMIT_PER_HOUR: "60"
  RATE_LIMIT_PER_DAY: "500"
  LLM_SESSION_LIMIT: "10"
  LLM_DAILY_LIMIT: "50"
  LLM_DAILY_BUDGET_USD: "100.0"
```

#### k8s/secrets.yaml (Base64 encoded)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: bot-secrets
  namespace: dev2prod-bot
type: Opaque
data:
  DATABASE_URL: <base64-encoded-postgres-url>
  REDIS_URL: <base64-encoded-redis-url>
  TELEGRAM_BOT_TOKEN: <base64-encoded-token>
  TELEGRAM_WEBHOOK_SECRET: <base64-encoded-secret>
  LONGCAT_API_KEY: <base64-encoded-key>
  SECRET_KEY: <base64-encoded-secret-key>
```

#### k8s/deployment-api.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bot-api
  namespace: dev2prod-bot
  labels:
    app: bot-api
    tier: backend
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: bot-api
  template:
    metadata:
      labels:
        app: bot-api
        tier: backend
    spec:
      containers:
      - name: bot-api
        image: your-registry/dev2prod-bot:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: bot-config
        - secretRef:
            name: bot-secrets
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
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        volumeMounts:
        - name: attachments
          mountPath: /app/attachments
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: attachments
        persistentVolumeClaim:
          claimName: attachments-pvc
      - name: logs
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: bot-api-service
  namespace: dev2prod-bot
spec:
  type: ClusterIP
  selector:
    app: bot-api
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
```

#### k8s/deployment-worker.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-worker
  namespace: dev2prod-bot
  labels:
    app: llm-worker
    tier: worker
spec:
  replicas: 5
  selector:
    matchLabels:
      app: llm-worker
  template:
    metadata:
      labels:
        app: llm-worker
        tier: worker
    spec:
      containers:
      - name: llm-worker
        image: your-registry/dev2prod-bot-worker:latest
        imagePullPolicy: Always
        envFrom:
        - configMapRef:
            name: bot-config
        - secretRef:
            name: bot-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

#### k8s/ingress.yaml
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bot-ingress
  namespace: dev2prod-bot
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - bot.dev2production.tech
    secretName: bot-tls-cert
  rules:
  - host: bot.dev2production.tech
    http:
      paths:
      - path: /webhook
        pathType: Prefix
        backend:
          service:
            name: bot-api-service
            port:
              number: 8000
      - path: /admin
        pathType: Prefix
        backend:
          service:
            name: bot-api-service
            port:
              number: 8000
```

#### k8s/hpa.yaml (Horizontal Pod Autoscaler)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: bot-api-hpa
  namespace: dev2prod-bot
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bot-api
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

#### k8s/pvc.yaml (Persistent Volume Claim)
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: attachments-pvc
  namespace: dev2prod-bot
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: standard
  resources:
    requests:
      storage: 50Gi
```

---

## Task 47: CI/CD Pipeline (GitHub Actions)

### .github/workflows/ci.yml
```yaml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install --no-root
    
    - name: Run flake8
      run: poetry run flake8 src tests
    
    - name: Run pylint
      run: poetry run pylint src
    
    - name: Run mypy
      run: poetry run mypy src

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_bot
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 3s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install --no-root
    
    - name: Run unit tests
      env:
        DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_bot
        REDIS_URL: redis://localhost:6379/0
      run: |
        poetry run pytest tests/unit -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Bandit security scan
      run: |
        pip install bandit
        bandit -r src -f json -o bandit-report.json
    
    - name: Run Safety check
      run: |
        pip install safety
        safety check --json
```

### .github/workflows/deploy.yml
```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]
    tags:
      - 'v*'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-
    
    - name: Build and push API image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
    
    - name: Build and push Worker image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile.worker
        push: true
        tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-worker:${{ github.sha }}

  deploy-k8s:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
    
    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBECONFIG }}" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
    
    - name: Update deployment image
      run: |
        kubectl set image deployment/bot-api \
          bot-api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
          -n dev2prod-bot
        
        kubectl set image deployment/llm-worker \
          llm-worker=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-worker:${{ github.sha }} \
          -n dev2prod-bot
    
    - name: Wait for rollout
      run: |
        kubectl rollout status deployment/bot-api -n dev2prod-bot
        kubectl rollout status deployment/llm-worker -n dev2prod-bot
    
    - name: Verify deployment
      run: |
        kubectl get pods -n dev2prod-bot
        kubectl get svc -n dev2prod-bot
```

---

## Task 48: Observability Stack

### monitoring/prometheus.yml
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'dev2prod-bot'
    environment: 'production'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - 'alerts/*.yml'

scrape_configs:
  - job_name: 'bot-api'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names: ['dev2prod-bot']
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: bot-api
        action: keep
      - source_labels: [__meta_kubernetes_pod_ip]
        target_label: __address__
        replacement: ${1}:8000
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### monitoring/alerts/bot-alerts.yml
```yaml
groups:
  - name: bot_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: HighLLMLatency
        expr: histogram_quantile(0.95, llm_response_time_seconds) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LLM response latency is high"
          description: "P95 latency is {{ $value }} seconds"

      - alert: LLMBudgetExceeded
        expr: llm_daily_cost_usd > 100
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Daily LLM budget exceeded"
          description: "Current spend: ${{ $value }}"

      - alert: HighEscalationRate
        expr: rate(conversations_escalated_total[1h]) > 0.3
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Escalation rate is high"
          description: "{{ $value }}% of conversations escalated"

      - alert: PodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod is crash looping"
          description: "{{ $labels.pod }} has restarted {{ $value }} times"

      - alert: DatabaseConnectionPoolExhausted
        expr: db_connection_pool_usage > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool near exhaustion"
          description: "{{ $value }}% of connections in use"
```

### src/utils/metrics.py (Prometheus Instrumentation)
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response
import time

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# LLM metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM API calls',
    ['model', 'status']
)

llm_response_time_seconds = Histogram(
    'llm_response_time_seconds',
    'LLM response time',
    ['model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

llm_tokens_used_total = Counter(
    'llm_tokens_used_total',
    'Total tokens consumed',
    ['model']
)

llm_daily_cost_usd = Gauge(
    'llm_daily_cost_usd',
    'Daily LLM cost in USD'
)

# Conversation metrics
conversations_started_total = Counter(
    'conversations_started_total',
    'Total conversations started'
)

conversations_escalated_total = Counter(
    'conversations_escalated_total',
    'Total conversations escalated',
    ['reason']
)

messages_processed_total = Counter(
    'messages_processed_total',
    'Total messages processed',
    ['sender_type']
)

# Lead metrics
leads_created_total = Counter(
    'leads_created_total',
    'Total leads created',
    ['score']
)

# Database metrics
db_connection_pool_usage = Gauge(
    'db_connection_pool_usage',
    'Database connection pool utilization'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation']
)

# Redis metrics
redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status']
)

# Rate limiting metrics
rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit violations',
    ['user_type']
)

async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")
```

### monitoring/grafana/dashboards/bot-dashboard.json
```json
{
  "dashboard": {
    "title": "Dev2Production Bot Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "LLM Response Time (P95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, llm_response_time_seconds)"
          }
        ]
      },
      {
        "title": "Daily LLM Cost",
        "targets": [
          {
            "expr": "llm_daily_cost_usd"
          }
        ]
      },
      {
        "title": "Active Conversations",
        "targets": [
          {
            "expr": "sum(conversations_started_total) - sum(conversations_escalated_total)"
          }
        ]
      },
      {
        "title": "Lead Conversion Rate",
        "targets": [
          {
            "expr": "rate(leads_created_total{score='hot'}[1h]) / rate(conversations_started_total[1h])"
          }
        ]
      }
    ]
  }
}
```

---

## Task 49: Operational Documentation

### docs/operations/KEY_ROTATION.md
```markdown
# Key Rotation Procedures

## Telegram Bot Token Rotation

**Frequency:** Every 90 days or immediately if compromised

1. **Generate new token:**
   ```bash
   # Contact @BotFather on Telegram
   # Send: /token
   # Follow prompts to regenerate
   ```

2. **Update secrets:**
   ```bash
   # Kubernetes
   kubectl create secret generic bot-secrets \
     --from-literal=TELEGRAM_BOT_TOKEN=<new-token> \
     --namespace=dev2prod-bot \
     --dry-run=client -o yaml | kubectl apply -f -
   
   # Trigger rolling restart
   kubectl rollout restart deployment/bot-api -n dev2prod-bot
   ```

3. **Verify webhook:**
   ```bash
   python scripts/set_webhook.py --verify
   ```

## LongCat API Key Rotation

1. Generate new key from LongCat dashboard
2. Update secret in Kubernetes
3. No restart required (config hot-reloaded)

## Database Password Rotation

1. **Create new user:**
   ```sql
   CREATE USER botuser_new WITH PASSWORD 'new_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE dev2prod_bot TO botuser_new;
   ```

2. **Update connection string in K8s secret**
3. **Rolling restart to pick up new credentials**
4. **Drop old user after verification**
```

### docs/operations/SCALING.md
```markdown
# Scaling Guide

## Horizontal Scaling

### API Pods
```bash
# Manual scaling
kubectl scale deployment bot-api --replicas=5 -n dev2prod-bot

# Auto-scaling (configured via HPA)
# Automatically scales between 3-10 pods based on CPU/memory
```

### Worker Pods
```bash
# Scale workers based on queue depth
kubectl scale deployment llm-worker --replicas=10 -n dev2prod-bot
```

## Vertical Scaling

Update resource limits in `k8s/deployment-api.yaml`:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Database Scaling

- **Read replicas:** Add read-only replicas for query distribution
- **Connection pooling:** Adjust `DATABASE_POOL_SIZE` in config
- **Partitioning:** Partition `messages` table by date

## Redis Scaling

- **Memory:** Increase `maxmemory` in redis.conf
- **Replication:** Add Redis replicas for high availability
- **Cluster mode:** Enable Redis Cluster for horizontal scaling
```

### docs/operations/BACKUP_RESTORE.md
```markdown
# Backup & Restore Procedures

## Database Backups

### Automated Daily Backups
```bash
# CronJob (runs daily at 2 AM)
0 2 * * * pg_dump -U botuser dev2prod_bot | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

### Manual Backup
```bash
kubectl exec -it postgres-pod -n dev2prod-bot -- \
  pg_dump -U botuser dev2prod_bot > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
# Stop API pods
kubectl scale deployment bot-api --replicas=0 -n dev2prod-bot

# Restore database
kubectl exec -i postgres-pod -n dev2prod-bot -- \
  psql -U botuser dev2prod_bot < backup_20250101.sql

# Restart API pods
kubectl scale deployment bot-api --replicas=3 -n dev2prod-bot
```

## Redis Backups

Redis persistence enabled with AOF (Append-Only File)

### Manual snapshot
```bash
kubectl exec -it redis-pod -n dev2prod-bot -- redis-cli BGSAVE
```

## File Attachments Backup

Backup PVC to S3:
```bash
kubectl exec -it bot-api-pod -n dev2prod-bot -- \
  aws s3 sync /app/attachments s3://backups/attachments-$(date +%Y%m%d)
```
```

---

## Task 50: Final Documentation

### README.md
```markdown
# Dev2Production Telegram Bot

AI-powered Telegram bot for dev2production.tech customer support, lead qualification, and project intake.

## 🚀 Features

- **Intelligent FAQ:** Instant answers to 40+ common questions with canned responses
- **Project Intake:** 6-step qualification flow with automated lead scoring
- **LLM Integration:** LongCat.chat API for complex queries (GPT-4, Claude)
- **Human Handoff:** Smart escalation to agent group with conversation context
- **File Uploads:** Secure file handling with validation and storage
- **Admin Dashboard:** Web UI for conversation monitoring and management
- **Multi-Agent Support:** RBAC with 4 role levels and claim system

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose
- Telegram Bot Token (from @BotFather)
- LongCat.chat API Key

## 🛠️ Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/dev2prod-bot.git
cd dev2prod-bot
```

### 2. Environment Setup
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run with Docker Compose
```bash
docker-compose up -d
```

### 4. Initialize Database
```bash
docker-compose exec bot-api poetry run alembic upgrade head
```

### 5. Set Telegram Webhook
```bash
docker-compose exec bot-api poetry run python scripts/set_webhook.py
```

### 6. Verify
```bash
# Check health
curl http://localhost:8000/health

# Test bot by sending /start on Telegram
```

## 📦 Project Structure

```
dev2prod-bot/
├── src/
│   ├── api/              # FastAPI routes
│   ├── services/         # Business logic
│   ├── db/               # Database models
│   ├── core/             # Configuration
│   └── utils/            # Utilities
├── tests/                # Test suite
├── k8s/                  # Kubernetes manifests
├── monitoring/           # Prometheus/Grafana configs
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## 🧪 Testing

```bash
# Unit tests
poetry run pytest tests/unit -v

# Integration tests
poetry run pytest tests/integration -v

# E2E tests
poetry run pytest tests/e2e -v --run-integration

# Coverage
poetry run pytest --cov=src --cov-report=html
```

## 📊 Monitoring

- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Admin Dashboard:** http://localhost:8000/admin

## 🚢 Deployment

### Development
```bash
docker-compose up -d
```

### Production (Kubernetes)
```bash
kubectl apply -f k8s/
```

See [docs/operations/DEPLOYMENT.md](docs/operations/DEPLOYMENT.md) for details.

## 📖 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Operations Manual](docs/operations/)

## 🔒 Security

- PII masking for logs
- Rate limiting (60/hour, 500/day per user)
- File upload validation
- SQL injection & XSS protection
- Secrets management with Kubernetes Secrets
- HTTPS-only webhooks

## 📈 KPIs

- Lead conversion rate: ≥25%
- LLM cost per conversation: <$0.15
- Human handoff rate: 10-20%
- Response latency (P95): <5s

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 📞 Support

- Email: support@dev2production.tech
- Telegram: @dev2production
```

### docs/ARCHITECTURE.md
```markdown
# Architecture Overview

## System Design

```mermaid
graph TB
    User[Telegram User] -->|Messages| TG[Telegram API]
    TG -->|Webhook| NX[NGINX Ingress]
    NX -->|HTTPS| API[Bot API Pods]
    API -->|Queries| PG[(PostgreSQL)]
    API -->|Cache/State| RD[(Redis)]
    API -->|Queue| Q[LLM Job Queue]
    Q -->|Process| WK[LLM Workers]
    WK -->|API Calls| LC[LongCat.chat]
    API -->|Escalate| AG[Agent Group]
    AG -->|Respond| TG
    API -->|Metrics| PR[Prometheus]
    PR -->|Visualize| GF[Grafana]
```

## Components

### Bot API (FastAPI)
- Webhook handler for Telegram updates
- Intent detection & routing
- Conversation management
- Agent handoff orchestration
- Admin dashboard

### LLM Workers
- Background job processors
- LongCat API integration
- Conversation context management
- Quota enforcement

### PostgreSQL
- User conversations
- Message history
- Lead data
- Agent assignments

### Redis
- Session state (1-hour TTL)
- Rate limiting counters
- LLM quota tracking
- Agent assignment cache

### Monitoring Stack
- Prometheus: Metrics collection
- Grafana: Visualization
- Alert Manager: Alerting

## Data Flow

### 1. User Message
```
User → Telegram → Webhook → API → Intent Detector
                                    ↓
                            [Canned Response]
                                    ↓
                            API → Telegram → User
```

### 2. LLM Flow
```
User → Telegram → Webhook → API → Queue → Worker → LongCat
                                                      ↓
User ← Telegram ← API ← Queue ← Worker ← Response ←─┘
```

### 3. Escalation Flow
```
User → API → Escalation Service → Agent Group (Telegram)
               ↓
         Update DB (status=escalated)
               ↓
Agent → Claim → API → Update Redis
               ↓
Agent Reply → API → User
```

## Scalability

- **Horizontal:** API pods auto-scale 3-10 based on CPU/memory
- **Vertical:** Increase pod resource limits
- **Database:** Read replicas for query distribution
- **Cache:** Redis cluster for high availability
- **Workers:** Scale workers independently based on queue depth

## Security

- Webhook secret validation
- HTTPS-only endpoints
- PII masking in logs
- Rate limiting per user
- RBAC for admin access
- Secrets managed via Kubernetes Secrets
```

---

## Implementation Checklist for Phase 6

- [ ] Test docker-compose.yml locally (all services healthy)
- [ ] Create Kubernetes namespace and apply manifests
- [ ] Configure container registry (Docker Hub, GHCR, ECR)
- [ ] Set up GitHub Actions CI/CD pipeline
- [ ] Configure Prometheus scraping targets
- [ ] Import Grafana dashboards
- [ ] Set up Alertmanager notifications (Slack, PagerDuty)
- [ ] Write operational runbooks (rotation, scaling, backup)
- [ ] Create architecture diagrams (Mermaid, draw.io)
- [ ] Write comprehensive README with quick start
- [ ] Document API endpoints (OpenAPI/Swagger)
- [ ] Create onboarding guide for new developers
- [ ] Perform load testing and optimize
- [ ] Set up SSL certificates (Let's Encrypt)
- [ ] Configure DNS and domain routing

**🎉 Project Complete! All 50 tasks documented and ready for implementation.**
