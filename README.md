# Canvas3T

A full-stack web application for creating, editing, uploading, and managing digital paintings. Built with Flask, React, and deployed on AWS EKS.

**Live URL**: http://canvas3t-alb-1075541864.ap-south-1.elb.amazonaws.com

---

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Local Development](#local-development)
- [Kubernetes / EKS Deployment](#kubernetes--eks-deployment)
  - [Prerequisites](#prerequisites)
  - [1. Create EKS Cluster](#1-create-eks-cluster)
  - [2. Install Required Add-ons](#2-install-required-add-ons)
  - [3. Build and Push Docker Images](#3-build-and-push-docker-images)
  - [4. Deploy Kubernetes Manifests](#4-deploy-kubernetes-manifests)
  - [5. Install AWS Load Balancer Controller](#5-install-aws-load-balancer-controller)
  - [6. Verify Deployment](#6-verify-deployment)
- [Configuration Reference](#configuration-reference)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Cleanup](#cleanup)

---

## Architecture

```
Internet
    │
    ▼
┌───────────────────────────────┐
│  AWS Application Load Balancer│  canvas3t-alb-*.ap-south-1.elb.amazonaws.com
│  (Provisioned by ALB Ingress) │
└───────────┬───────────────────┘
            │  /        → Frontend (React + Nginx, port 4173)
            │  /api/*   → Backend  (Flask + Gunicorn, port 5000)
            │  /media/* → Backend  (image serving)
            ▼
┌───────────────────────────────────────┐
│           EKS Cluster (ap-south-1)    │
│                                       │
│  canvas3t namespace                   │
│  ┌─────────────────────────────────┐  │
│  │  canvas3t-frontend (2 pods)     │  │
│  │  Nginx proxies /api & /media    │  │
│  │  to canvas3t-backend service    │  │
│  └─────────────────────────────────┘  │
│  ┌─────────────────────────────────┐  │
│  │  canvas3t-backend  (1 pod)      │  │
│  │  Flask + Gunicorn               │  │
│  │  Mounts EBS volumes:            │  │
│  │    /data/db     → SQLite DB     │  │
│  │    /data/images → Uploaded imgs │  │
│  └─────────────────────────────────┘  │
│                                       │
│  kube-system namespace                │
│  ┌───────────────────────────────┐    │
│  │  aws-load-balancer-controller │    │
│  │  aws-ebs-csi-driver           │    │
│  └───────────────────────────────┘    │
└───────────────────────────────────────┘
            │
┌───────────┴───────────────────────┐
│  AWS EBS Volumes (ap-south-1)     │
│  canvas3t-db-ebs     (5 GB  gp3)  │
│  canvas3t-images-ebs (20 GB gp3)  │
└───────────────────────────────────┘
            │
┌───────────┴───────────────────────┐
│  Amazon ECR                       │
│  canvas3t-backend:latest          │
│  canvas3t-frontend:latest         │
└───────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Zustand, React Query, Nginx |
| Backend | Python 3.11, Flask, Gunicorn, SQLAlchemy, SQLite |
| Container registry | Amazon ECR |
| Orchestration | Kubernetes 1.36 on AWS EKS |
| Load balancer | AWS ALB via `aws-load-balancer-controller` |
| Persistent storage | AWS EBS (gp3) via `aws-ebs-csi-driver` |
| Auth | `itsdangerous` signed tokens (7-day expiry) |
| Images | Pillow — thumbnails auto-generated on upload |

---

## Local Development

**Prerequisites**: Docker Desktop, Node 18+, Python 3.11+

```powershell
# Clone the repo and start everything with Docker Compose
docker compose up -d

# Frontend: http://localhost:5173
# Backend API: http://localhost:5000/api/health
```

The compose file mounts `./backend` as a live volume so Flask restarts on code changes.

**Run backend only (no Docker):**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
flask run --host=0.0.0.0 --port=5000
```

**Run frontend only (no Docker):**
```powershell
cd frontend
npm install
npm run dev   # http://localhost:5173
```

---

## Kubernetes / EKS Deployment

> All commands are tested on **Windows 11** with PowerShell and an **ap-south-1** cluster.
> Adjust `--region` and account IDs as needed.

### Prerequisites

Install the required CLI tools:

```powershell
winget install Amazon.AWSCLI
winget install Kubernetes.kubectl
winget install eksctl.eksctl
winget install Helm.Helm
# Docker Desktop: https://www.docker.com/products/docker-desktop
```

Configure AWS credentials:

```powershell
aws configure
# AWS Access Key ID:     <your-key>
# AWS Secret Access Key: <your-secret>
# Default region:        ap-south-1
# Default output format: json

# Verify
aws sts get-caller-identity
```

---

### 1. Create EKS Cluster

```powershell
eksctl create cluster `
  --name canvas3t-cluster `
  --region ap-south-1 `
  --version 1.36 `
  --nodegroup-name canvas3t-nodes `
  --node-type t3.medium `
  --nodes 2 `
  --managed
```

This takes 15–20 minutes and automatically configures `kubectl`.

```powershell
kubectl get nodes   # Should show 2 Ready nodes
```

---

### 2. Install Required Add-ons

#### EBS CSI Driver (for persistent volumes)

```powershell
eksctl create addon `
  --name aws-ebs-csi-driver `
  --cluster canvas3t-cluster `
  --region ap-south-1 `
  --force

# Verify — wait for ACTIVE status
eksctl get addon --name aws-ebs-csi-driver --cluster canvas3t-cluster --region ap-south-1
```

#### OIDC Provider (required for IRSA — IAM roles for service accounts)

```powershell
eksctl utils associate-iam-oidc-provider `
  --region ap-south-1 `
  --cluster canvas3t-cluster `
  --approve
```

---

### 3. Build and Push Docker Images

#### Create ECR repositories

```powershell
$REGION = "ap-south-1"
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)

aws ecr create-repository --repository-name canvas3t-backend  --region $REGION
aws ecr create-repository --repository-name canvas3t-frontend --region $REGION
```

#### Login to ECR

```powershell
aws ecr get-login-password --region $REGION |
  docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
```

#### Build and push backend

```powershell
# From project root
docker build -t canvas3t-backend:latest -f Dockerfile .

docker tag  canvas3t-backend:latest "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/canvas3t-backend:latest"
docker push "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/canvas3t-backend:latest"
```

#### Build and push frontend

```powershell
# Frontend uses a multi-stage Dockerfile (Rust WASM → Node build → Nginx)
docker build -t canvas3t-frontend:latest -f frontend/Dockerfile .

docker tag  canvas3t-frontend:latest "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/canvas3t-frontend:latest"
docker push "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/canvas3t-frontend:latest"
```

> **Tip:** After any code change, rebuild with `--no-cache` and push again, then run `kubectl rollout restart deployment/<name> -n canvas3t`.

---

### 4. Deploy Kubernetes Manifests

All manifests live in `kubernetes/`. Apply them in order:

#### 4a. Namespace and ConfigMap

```powershell
kubectl apply -f kubernetes/00-namespace-config.yaml
```

This creates the `canvas3t` namespace, `canvas3t-config` ConfigMap, and `canvas3t-secrets` Secret.

Key ConfigMap values:

| Key | Value |
|---|---|
| `DB_PATH` | `/data/db/app.db` |
| `DB_DIR` | `/data/db` |
| `IMAGE_DIR` | `/data/images` |
| `THUMBNAIL_DIR` | `/data/images/thumbnails` |
| `RATE_LIMIT` | `200/minute` |

> **Important:** The backend volume mounts to `/data`. Make sure `DB_PATH` and `IMAGE_DIR` use `/data/...` not `/app/...`.

#### 4b. Storage (EBS PVCs)

```powershell
kubectl apply -f kubernetes/01-storage.yaml
```

Creates:
- `canvas3t-ebs` StorageClass using `ebs.csi.aws.com` provisioner (gp3)
- `canvas3t-db-ebs` PVC — 5 Gi for SQLite database
- `canvas3t-images-ebs` PVC — 20 Gi for uploaded images

> EBS volumes are `ReadWriteOnce` — they can only attach to one node at a time. This is why the backend must run as **1 replica**.

#### 4c. ECR Pull Secret

```powershell
$REGION = "ap-south-1"
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$ECR_PASS = aws ecr get-login-password --region $REGION

kubectl create secret docker-registry ecr-secret `
  --namespace canvas3t `
  --docker-server="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com" `
  --docker-username=AWS `
  --docker-password="$ECR_PASS"
```

#### 4d. Backend Deployment

```powershell
kubectl apply -f kubernetes/02-backend-deployment.yaml
```

Key settings in this deployment:
- **1 replica** (required — EBS `ReadWriteOnce`)
- Strategy: `Recreate` (not RollingUpdate, avoids dual-attach)
- Volume mounts: `/data/db` and `/data/images` on EBS PVCs
- Liveness probe: `GET /api/health` (every 30s)
- Readiness probe: `GET /api/health` (every 10s)

#### 4e. Frontend Deployment

```powershell
kubectl apply -f kubernetes/03-frontend-deployment.yaml
```

- 2 replicas (stateless, safe to scale)
- Nginx proxies `/api/*` and `/media/*` to `canvas3t-backend:5000`

#### 4f. HPA (Horizontal Pod Autoscaler)

```powershell
kubectl apply -f kubernetes/05-hpa.yaml
```

> **Important:** The backend HPA must have `minReplicas: 1` and `maxReplicas: 1` because EBS volumes cannot be shared across pods.

```powershell
# Verify/fix backend HPA after applying
kubectl patch hpa canvas3t-backend-hpa -n canvas3t `
  --type merge -p '{"spec":{"minReplicas":1,"maxReplicas":1}}'
```

---

### 5. Install AWS Load Balancer Controller

The ALB controller provisions an AWS Application Load Balancer from your Ingress resource.

#### Create IAM Policy

```powershell
curl -o alb-iam-policy.json `
  https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json

aws iam create-policy `
  --policy-name AWSLoadBalancerControllerIAMPolicy `
  --policy-document file://alb-iam-policy.json
```

#### Create IAM Service Account

```powershell
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)

eksctl create iamserviceaccount `
  --cluster canvas3t-cluster `
  --namespace kube-system `
  --name aws-load-balancer-controller `
  --attach-policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy" `
  --approve `
  --region ap-south-1
```

#### Install via Helm

```powershell
$VPC_ID = (aws eks describe-cluster `
  --name canvas3t-cluster `
  --region ap-south-1 `
  --query "cluster.resourcesVpcConfig.vpcId" `
  --output text)

helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller `
  -n kube-system `
  --set clusterName=canvas3t-cluster `
  --set serviceAccount.create=false `
  --set serviceAccount.name=aws-load-balancer-controller `
  --set region=ap-south-1 `
  --set vpcId=$VPC_ID
```

#### Deploy Ingress

```powershell
kubectl apply -f kubernetes/04-ingress-network.yaml
```

The ingress is configured with these annotations:

```yaml
alb.ingress.kubernetes.io/scheme: internet-facing
alb.ingress.kubernetes.io/target-type: ip
alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}]'
```

It includes a wildcard rule (no `host:` field) so the app is accessible directly via the ALB URL — no custom domain required.

---

### 6. Verify Deployment

```powershell
# All pods should be Running, 0 restarts
kubectl get pods -n canvas3t

# PVCs should be Bound
kubectl get pvc -n canvas3t

# Ingress should show an ADDRESS
kubectl get ingress canvas3t-ingress -n canvas3t

# ALB controller should be running
kubectl get deployment -n kube-system aws-load-balancer-controller
```

Get your application URL:

```powershell
kubectl get ingress canvas3t-ingress -n canvas3t `
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

Test it:

```powershell
$ALB = "http://$(kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')"

# Health check
Invoke-WebRequest "$ALB/api/health" | Select-Object -ExpandProperty Content

# Register
Invoke-WebRequest -Method POST "$ALB/api/auth/register" `
  -ContentType "application/json" `
  -Body '{"username":"myuser","password":"Pass1234","email":"me@test.com"}' |
  Select-Object -ExpandProperty Content

# Login
Invoke-WebRequest -Method POST "$ALB/api/auth/login" `
  -ContentType "application/json" `
  -Body '{"username":"myuser","password":"Pass1234"}' |
  Select-Object -ExpandProperty Content
```

#### Default credentials (auto-created on first boot)

| Username | Password |
|---|---|
| `demo` | `demo123456` |

---

## Configuration Reference

### ConfigMap — `canvas3t-config`

| Variable | Default | Description |
|---|---|---|
| `FLASK_APP` | `app` | Flask app module |
| `FLASK_ENV` | `production` | Flask environment |
| `DB_PATH` | `/data/db/app.db` | SQLite database path |
| `DB_DIR` | `/data/db` | Database directory |
| `IMAGE_DIR` | `/data/images` | Uploaded images root |
| `THUMBNAIL_DIR` | `/data/images/thumbnails` | Thumbnail storage |
| `DATA_DIR` | `/data` | Persistent data root |
| `RESULTS_PER_PAGE` | `24` | Gallery pagination |
| `ENABLE_RATE_LIMITS` | `true` | Enable rate limiting |
| `RATE_LIMIT` | `200/minute` | Per-IP rate limit |

### Secret — `canvas3t-secrets`

| Key | Description |
|---|---|
| `SECRET_KEY` | Flask secret key for token signing — change before production |
| `JWT_SECRET` | Reserved for future JWT use |
| `DB_PASSWORD` | Reserved for future PostgreSQL migration |

---

## API Reference

### Auth

| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | `{username, email, password}` | Register and get token |
| `POST` | `/api/auth/login` | `{username, password}` | Login and get token |
| `POST` | `/api/auth/verify` | — (Bearer token header) | Verify token validity |

### Users

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/users` | Register user (legacy — use `/api/auth/register`) |
| `GET` | `/api/users` | List all users |
| `GET` | `/api/users/<id>` | Get user by ID |

### Paintings

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/paintings` | List public paintings (or user's with `?user_id=`) |
| `POST` | `/api/paintings` | Upload image (multipart/form-data) |
| `GET` | `/api/paintings/<id>` | Get painting by ID |
| `PUT` | `/api/paintings/<id>` | Update painting metadata or image |
| `POST` | `/api/paintings/import-url` | Import image from remote URL |

### Media

| Method | Path | Description |
|---|---|---|
| `GET` | `/media/images/<path>` | Serve uploaded image or thumbnail |

All authenticated endpoints expect: `Authorization: Bearer <token>`

---

## Troubleshooting

### Pod keeps restarting

```powershell
# Check what's killing it
kubectl describe pod -n canvas3t -l app=canvas3t-backend

# Common cause: liveness probe returning 429 (rate limit)
# Fix: ensure /api/health is excluded from rate limiting (check rate_limit.py)
# Then rebuild with --no-cache and redeploy
```

### 503 Service Temporarily Unavailable

```powershell
# Pod is down — check status
kubectl get pods -n canvas3t

# Check logs from previous (crashed) container
kubectl logs -n canvas3t deployment/canvas3t-backend --previous --tail=30
```

### 400 Bad Request on register/login

The request body isn't being parsed as JSON. All `request.get_json()` calls must use `force=True, silent=True`:

```python
data = request.get_json(force=True, silent=True) or {}
```

### PVCs stuck in Pending

```powershell
kubectl describe pvc canvas3t-db-ebs -n canvas3t
```

Common causes:
- EBS CSI driver not installed → `eksctl create addon --name aws-ebs-csi-driver ...`
- StorageClass using wrong provisioner (`kubernetes.io/aws-ebs` vs `ebs.csi.aws.com`) → use `ebs.csi.aws.com`

### ALB not provisioning (Ingress has no ADDRESS)

```powershell
# Check ALB controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller --tail=30

# Common causes:
# 1. OIDC provider not associated → eksctl utils associate-iam-oidc-provider
# 2. IAM service account not created → eksctl create iamserviceaccount
# 3. ALB controller not installed → helm install aws-load-balancer-controller
```

### Data lost after pod restart

EBS volumes are persistent but the pod must mount them correctly. Verify:

```powershell
kubectl exec -n canvas3t deployment/canvas3t-backend -- ls -la /data/db/
kubectl exec -n canvas3t deployment/canvas3t-backend -- ls -la /data/images/
```

If empty, the ConfigMap paths are wrong — ensure `DB_PATH=/data/db/app.db` not `/app/db/app.db`.

### Two backend pods fighting over SQLite

EBS volumes are `ReadWriteOnce`. If you have 2 backend replicas, the second pod can't attach the volume.

```powershell
# Fix: lock backend to 1 replica via HPA
kubectl patch hpa canvas3t-backend-hpa -n canvas3t `
  --type merge -p '{"spec":{"minReplicas":1,"maxReplicas":1}}'

kubectl scale deployment canvas3t-backend -n canvas3t --replicas=1
```

---

## Cleanup

```powershell
# Delete all app resources
kubectl delete namespace canvas3t

# Delete EKS cluster (takes 5-10 min)
eksctl delete cluster --name canvas3t-cluster --region ap-south-1

# Delete ECR repositories
aws ecr delete-repository --repository-name canvas3t-backend  --force --region ap-south-1
aws ecr delete-repository --repository-name canvas3t-frontend --force --region ap-south-1

# Delete IAM policy
aws iam delete-policy `
  --policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy
```

> EBS volumes use `reclaimPolicy: Retain` — they are not deleted automatically. Clean them up manually in the AWS console or:
> ```powershell
> aws ec2 describe-volumes --filters "Name=tag:kubernetes.io/cluster/canvas3t-cluster,Values=owned" --query "Volumes[].VolumeId" --output text |
>   ForEach-Object { aws ec2 delete-volume --volume-id $_ }
> ```

---

## Estimated Monthly Cost (ap-south-1)

| Resource | Cost |
|---|---|
| EKS cluster fee | ~$73 |
| 2× t3.medium nodes | ~$55 |
| Application Load Balancer | ~$18 |
| EBS gp3 25 GB total | ~$2 |
| ECR storage | ~$1 |
| **Total** | **~$149/month** |

To reduce costs: use `t3.small` nodes (~$27/month each) or enable Spot Instances.
