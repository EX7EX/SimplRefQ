# Deployment Guide

## Prerequisites

- Python 3.8+
- Node.js 14+
- Docker
- Kubernetes (for production)
- AWS/GCP account (for cloud deployment)

## Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SimplRefQ.git
cd SimplRefQ
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
python scripts/init_db.py
```

6. Start the development server:
```bash
python SimplRefQ.py
```

## Docker Deployment

1. Build the Docker image:
```bash
docker build -t simplrefq .
```

2. Run the container:
```bash
docker run -d \
  --name simplrefq \
  -p 5000:5000 \
  --env-file .env \
  simplrefq
```

## Kubernetes Deployment

1. Create Kubernetes secrets:
```bash
kubectl create secret generic simplrefq-secrets \
  --from-file=.env
```

2. Apply Kubernetes manifests:
```bash
kubectl apply -f k8s/
```

3. Verify deployment:
```bash
kubectl get pods
kubectl get services
```

## Cloud Deployment (AWS)

1. Set up EKS cluster:
```bash
eksctl create cluster \
  --name simplrefq-cluster \
  --region us-west-2 \
  --node-type t3.medium \
  --nodes 3
```

2. Deploy using Helm:
```bash
helm install simplrefq ./helm
```

3. Configure load balancer:
```bash
kubectl apply -f k8s/ingress.yaml
```

## CI/CD Pipeline

1. GitHub Actions workflow:
```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Kubernetes
        run: |
          kubectl apply -f k8s/
```

## Monitoring Setup

1. Install Prometheus and Grafana:
```bash
helm install prometheus stable/prometheus
helm install grafana stable/grafana
```

2. Configure alerts:
```yaml
groups:
- name: simplrefq
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected
```

## Backup and Recovery

1. Database backup:
```bash
pg_dump -U postgres simplrefq > backup.sql
```

2. Restore from backup:
```bash
psql -U postgres simplrefq < backup.sql
```

## Scaling Configuration

1. Horizontal Pod Autoscaling:
```yaml
apiVersion: autoscaling/v2beta2
kind: HorizontalPodAutoscaler
metadata:
  name: simplrefq
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: simplrefq
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Security Configuration

1. SSL/TLS setup:
```bash
kubectl create secret tls simplrefq-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem
```

2. Network policies:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: simplrefq-policy
spec:
  podSelector:
    matchLabels:
      app: simplrefq
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: simplrefq
```

## Maintenance Procedures

1. Database migration:
```bash
alembic upgrade head
```

2. Cache clearing:
```bash
redis-cli FLUSHALL
```

3. Log rotation:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: logrotate-config
data:
  logrotate.conf: |
    /var/log/simplrefq/*.log {
      daily
      rotate 7
      compress
      missingok
      notifempty
    }
```

## Troubleshooting

1. Check logs:
```bash
kubectl logs -f deployment/simplrefq
```

2. Monitor metrics:
```bash
kubectl top pods
```

3. Debug services:
```bash
kubectl describe pod simplrefq-xxxxx
```

## Rollback Procedures

1. Rollback deployment:
```bash
kubectl rollout undo deployment/simplrefq
```

2. Restore database:
```bash
psql -U postgres simplrefq < backup.sql
```

3. Clear cache:
```bash
redis-cli FLUSHALL
``` 