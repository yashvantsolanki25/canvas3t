# Canvas3T — Art Gallery Platform

A full-stack art gallery application with a Python/Flask REST API backend, React + TypeScript frontend, and Rust/WASM canvas editor. Deployed on AWS EKS at **https://myart.run.place**.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Local Development](#local-development)
5. [AWS Setup](#aws-setup)
6. [Build & Push Docker Images to ECR](#build--push-docker-images-to-ecr)
7. [Create EKS Cluster](#create-eks-cluster)
8. [Install EKS Add-ons](#install-eks-add-ons)
9. [Deploy to Kubernetes](#deploy-to-kubernetes)
10. [DNS & HTTPS Setup](#dns--https-setup)
11. [Verify Everything Works](#verify-everything-works)
12. [File Reference](#file-reference)
13. [Troubleshooting](#troubleshooting)
14. [Updating the Application](#updating-the-application)

---

## Architecture Overview

```
User Browser
     │
     ▼
Route 53 (myart.run.place)
     │
     ▼
AWS ALB (canvas3t-alb)  ← managed by AWS Load Balancer Controller
     │
     ├── /api/*   ──► canvas3t-backend (Flask/Gunicorn, port 5000)
     ├── /media/* ──► canvas3t-backend (Flask/Gunicorn, port 5000)
     └── /*       ──► canvas3t-frontend (Nginx, port 4173)

EKS Cluster (ap-south-1)
├── canvas3t namespace
│   ├── Deployment: canvas3t-backend  (1 replica)
│   ├── Deployment: canvas3t-frontend (2 replicas)
│   ├── Service: canvas3t-backend  (ClusterIP :5000)
│   ├── Service: canvas3t-frontend (ClusterIP :4173)
│   ├── Ingress: canvas3t-ingress  (ALB)
│   ├── PVC: canvas3t-db-ebs     (5Gi EBS gp3 — SQLite)
│   └── PVC: canvas3t-images-ebs (20Gi EBS gp3 — uploads)
└── kube-system
    └── aws-load-balancer-controller
```

**Stack:**
- Backend: Python 3.11, Flask 3.0, SQLAlchemy, SQLite, Gunicorn
- Frontend: React 18, TypeScript, Vite, Zustand, Nginx
- Canvas: Rust compiled to WebAssembly via wasm-pack
- Infrastructure: AWS EKS, ECR, ALB, EBS, ACM, Route 53

---

## Project Structure

```
.
├── backend/                  # Flask API
│   ├── app/
│   │   ├── __init__.py       # App factory, blueprint registration
│   │   ├── config.py         # Config from environment variables
│   │   ├── extensions.py     # DB, CORS, rate limiter
│   │   ├── models.py         # User + Painting SQLAlchemy models
│   │   ├── schemas.py        # Marshmallow serialization schemas
│   │   ├── media.py          # Legacy media blueprint (unused)
│   │   ├── api/
│   │   │   ├── auth.py       # POST /api/auth/register, /login, /verify
│   │   │   ├── users.py      # GET/POST /api/users
│   │   │   ├── paintings.py  # CRUD /api/paintings
│   │   │   ├── search.py     # GET /api/search
│   │   │   └── media.py      # GET /media/images/<path>
│   │   └── utils/
│   │       ├── rate_limit.py # In-memory rate limiter
│   │       ├── storage.py    # Image save/delete helpers
│   │       └── thumbnails.py # Thumbnail generation
│   ├── wsgi.py               # Gunicorn entry point
│   ├── manage.py             # Flask CLI (init-db command)
│   └── requirements.txt
├── frontend/                 # React + TypeScript SPA
│   ├── src/
│   │   ├── api/              # Axios API clients
│   │   ├── components/       # UI components
│   │   ├── store/            # Zustand state stores
│   │   └── wasm/             # Rust/WASM canvas bridge
│   ├── Dockerfile            # Multi-stage: Rust → Node → Nginx
│   └── nginx.conf
├── wasm/                     # Rust canvas engine source
├── Dockerfile                # Backend image
├── docker-compose.yml        # Local development
├── canvas3t-backend-deployment.yaml  # K8s Deployment + Service
├── canvas3t-configmap.yaml           # K8s ConfigMap (env vars)
├── canvas3t-secrets.yaml             # K8s Secret template
├── canvas3t-storage.yaml             # StorageClass + PVCs
├── canvas3t-ingress-updated.yaml     # ALB Ingress (PRODUCTION)
├── canvas3t-https.yaml               # Alt: nginx-ingress + cert-manager
└── alb-iam-policy.json               # IAM policy for ALB controller
```

---

## Prerequisites

Install these tools before starting:

```powershell
# AWS CLI v2
winget install Amazon.AWSCLI

# kubectl
winget install Kubernetes.kubectl

# eksctl
winget install eksctl.eksctl

# Docker Desktop
winget install Docker.DockerDesktop

# Verify
aws --version        # aws-cli/2.x
kubectl version --client
eksctl version
docker --version
```

Configure AWS credentials:

```powershell
aws configure
# AWS Access Key ID:     <your-access-key>
# AWS Secret Access Key: <your-secret-key>
# Default region:        ap-south-1
# Default output format: json

# Confirm identity
aws sts get-caller-identity
```

---

## Local Development

Run the full stack locally with Docker Compose. No Kubernetes needed.

```powershell
# From project root
docker-compose up --build

# Backend available at: http://localhost:5000/api/health
# Frontend available at: http://localhost:5173
```

The `docker-compose.yml` mounts `./backend` as a live volume so Python code changes apply without rebuilding. Data persists in named Docker volumes `canvas3t_images` and `canvas3t_db`.

To reset local data:
```powershell
docker-compose down -v   # -v removes volumes
docker-compose up --build
```

---

## AWS Setup

### Step 1 — Create ECR Repositories

```powershell
$REGION = "ap-south-1"
$ACCOUNT = (aws sts get-caller-identity --query Account --output text)

aws ecr create-repository --repository-name canvas3t-backend `
  --region $REGION --image-scanning-configuration scanOnPush=true

aws ecr create-repository --repository-name canvas3t-frontend `
  --region $REGION --image-scanning-configuration scanOnPush=true

Write-Host "ECR registry: $ACCOUNT.dkr.ecr.$REGION.amazonaws.com"
```

### Step 2 — Create IAM Policy for ALB Controller

The ALB controller needs permissions to create and manage load balancers. `alb-iam-policy.json` in the repo root contains the exact policy.

```powershell
aws iam create-policy `
  --policy-name AWSLoadBalancerControllerIAMPolicy `
  --policy-document file://alb-iam-policy.json `
  --region $REGION
```

### Step 3 — Request ACM Certificate (for HTTPS)

```powershell
# Request certificate for your domain
aws acm request-certificate `
  --domain-name myart.run.place `
  --validation-method DNS `
  --region $REGION

# Get the certificate ARN — you'll need it later
aws acm list-certificates --region $REGION
```

After requesting, go to **AWS Console → ACM → Certificate** and add the CNAME validation record to your DNS provider. Wait until status shows **Issued** before continuing.

---

## Build & Push Docker Images to ECR

Run this every time you change backend or frontend code.

```powershell
$REGION   = "ap-south-1"
$ACCOUNT  = (aws sts get-caller-identity --query Account --output text)
$ECR      = "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"

# Login to ECR
aws ecr get-login-password --region $REGION `
  | docker login --username AWS --password-stdin $ECR

# --- Backend ---
docker build -f Dockerfile -t canvas3t-backend:latest .
docker tag canvas3t-backend:latest $ECR/canvas3t-backend:latest
docker push $ECR/canvas3t-backend:latest

# --- Frontend ---
# Multi-stage build: compiles Rust WASM, then Vite, then packages into Nginx
docker build -f frontend/Dockerfile -t canvas3t-frontend:latest .
docker tag canvas3t-frontend:latest $ECR/canvas3t-frontend:latest
docker push $ECR/canvas3t-frontend:latest
```

> The frontend Dockerfile has 4 stages: **wasm** (Rust → .wasm), **deps** (npm install), **builder** (Vite build), **runner** (Nginx). The wasm stage takes ~6 minutes on first build; subsequent builds use the Docker cache.

---

## Create EKS Cluster

This creates a managed EKS cluster with 2 worker nodes. Takes 15–20 minutes.

```powershell
eksctl create cluster `
  --name canvas3t-cluster `
  --region ap-south-1 `
  --version 1.28 `
  --nodegroup-name canvas3t-nodes `
  --node-type t3.medium `
  --nodes 2 `
  --nodes-min 1 `
  --nodes-max 4 `
  --managed `
  --with-oidc

# eksctl automatically updates your kubeconfig
kubectl get nodes   # should show 2 nodes in Ready state
```

The `--with-oidc` flag enables IAM Roles for Service Accounts (IRSA), required for the ALB controller to access AWS APIs.

---

## Install EKS Add-ons

### EBS CSI Driver (required for PersistentVolumes)

```powershell
# Create IAM role for EBS CSI driver
eksctl create iamserviceaccount `
  --name ebs-csi-controller-sa `
  --namespace kube-system `
  --cluster canvas3t-cluster `
  --region ap-south-1 `
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy `
  --approve `
  --role-only `
  --role-name AmazonEKS_EBS_CSI_DriverRole

# Install the add-on
$ACCOUNT = (aws sts get-caller-identity --query Account --output text)
aws eks create-addon `
  --cluster-name canvas3t-cluster `
  --addon-name aws-ebs-csi-driver `
  --service-account-role-arn arn:aws:iam::${ACCOUNT}:role/AmazonEKS_EBS_CSI_DriverRole `
  --region ap-south-1

# Verify
kubectl get pods -n kube-system | Select-String "ebs-csi"
```

### AWS Load Balancer Controller (required for ALB Ingress)

```powershell
$ACCOUNT = (aws sts get-caller-identity --query Account --output text)
$REGION  = "ap-south-1"

# Create IAM service account for the controller
eksctl create iamserviceaccount `
  --cluster canvas3t-cluster `
  --namespace kube-system `
  --name aws-load-balancer-controller `
  --attach-policy-arn arn:aws:iam::${ACCOUNT}:policy/AWSLoadBalancerControllerIAMPolicy `
  --override-existing-serviceaccounts `
  --approve `
  --region $REGION

# Install via Helm
helm repo add eks https://aws.github.io/eks-charts
helm repo update

$VPC_ID = (aws eks describe-cluster --name canvas3t-cluster `
  --region $REGION --query "cluster.resourcesVpcConfig.vpcId" --output text)

helm install aws-load-balancer-controller eks/aws-load-balancer-controller `
  -n kube-system `
  --set clusterName=canvas3t-cluster `
  --set serviceAccount.create=false `
  --set serviceAccount.name=aws-load-balancer-controller `
  --set region=$REGION `
  --set vpcId=$VPC_ID

# Verify controller is running
kubectl get deployment -n kube-system aws-load-balancer-controller
```

---

## Deploy to Kubernetes

Run these commands in order. All files are in the project root.

### Step 1 — Create Namespace

```powershell
kubectl create namespace canvas3t
```

### Step 2 — Create ECR Image Pull Secret

The backend deployment needs this to pull images from your private ECR.

```powershell
$REGION  = "ap-south-1"
$ACCOUNT = (aws sts get-caller-identity --query Account --output text)
$ECR_PASS = (aws ecr get-login-password --region $REGION)

kubectl create secret docker-registry ecr-secret `
  --docker-server="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com" `
  --docker-username=AWS `
  --docker-password=$ECR_PASS `
  -n canvas3t
```

> The ECR login token expires every 12 hours. If pods fail to pull images later, re-run this command to refresh the secret.

### Step 3 — Create Application Secret

Generate a strong secret key and create the Kubernetes secret. Do **not** commit real values to git — `canvas3t-secrets.yaml` is in `.gitignore`.

```powershell
# Generate a secure random key
$SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")

kubectl create secret generic canvas3t-secrets `
  --from-literal=SECRET_KEY="$SECRET_KEY" `
  -n canvas3t

# Verify
kubectl get secret canvas3t-secrets -n canvas3t
```

### Step 4 — Apply ConfigMap

`canvas3t-configmap.yaml` sets all non-secret environment variables for the backend pod.

```powershell
kubectl apply -f canvas3t-configmap.yaml
```

| Key | Value | Purpose |
|---|---|---|
| `FLASK_APP` | `app` | Gunicorn entry module |
| `FLASK_ENV` | `production` | Disables debug mode |
| `DB_PATH` | `/data/db/app.db` | SQLite file on EBS PVC |
| `IMAGE_DIR` | `/data/images` | Image storage on EBS PVC |
| `THUMBNAIL_DIR` | `/data/images/thumbnails` | Auto-created subdirectory |
| `RESULTS_PER_PAGE` | `24` | Gallery pagination |
| `RATE_LIMIT` | `200/minute` | Per-IP rate limit |

### Step 5 — Apply Storage

`canvas3t-storage.yaml` creates the StorageClass and two PersistentVolumeClaims backed by EBS gp3 volumes. Data persists across pod restarts and redeployments.

```powershell
kubectl apply -f canvas3t-storage.yaml

# Wait for PVCs — they stay Pending until a pod claims them (WaitForFirstConsumer)
kubectl get pvc -n canvas3t
# NAME                  STATUS    CAPACITY
# canvas3t-db-ebs       Pending   —         ← normal, binds on first pod start
# canvas3t-images-ebs   Pending   —         ← normal
```

### Step 6 — Deploy Backend

`canvas3t-backend-deployment.yaml` creates:
- **Deployment** with 1 replica, `Recreate` strategy (safe for EBS `ReadWriteOnce`)
- **Service** (ClusterIP) exposing port 5000
- Startup, readiness, and liveness probes on `/api/health`
- Volume mounts: `/data/db` (database) and `/data/images` (uploads)

Update the image URL in the file to match your account:
```yaml
image: YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/canvas3t-backend:latest
```

```powershell
kubectl apply -f canvas3t-backend-deployment.yaml

# Watch the pod start up
kubectl get pods -n canvas3t -w

# Check logs
kubectl logs -n canvas3t deployment/canvas3t-backend --follow
```

You should see:
```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:5000
[INFO] app - Database tables created/verified
```

### Step 7 — Deploy Frontend

The frontend deployment is defined inline below. Create a file `canvas3t-frontend-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: canvas3t-frontend
  namespace: canvas3t
spec:
  replicas: 2
  selector:
    matchLabels:
      app: canvas3t-frontend
  template:
    metadata:
      labels:
        app: canvas3t-frontend
    spec:
      containers:
        - name: frontend
          image: YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/canvas3t-frontend:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 4173
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 250m
              memory: 256Mi
          readinessProbe:
            httpGet:
              path: /
              port: 4173
            initialDelaySeconds: 5
            periodSeconds: 10
      imagePullSecrets:
        - name: ecr-secret
---
apiVersion: v1
kind: Service
metadata:
  name: canvas3t-frontend
  namespace: canvas3t
spec:
  type: ClusterIP
  selector:
    app: canvas3t-frontend
  ports:
    - port: 4173
      targetPort: 4173
```

```powershell
kubectl apply -f canvas3t-frontend-deployment.yaml
kubectl get pods -n canvas3t
```

### Step 8 — Apply Ingress

`canvas3t-ingress-updated.yaml` creates an internet-facing ALB with HTTPS via ACM.

Before applying, update the certificate ARN to match yours:
```yaml
alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-south-1:YOUR_ACCOUNT:certificate/YOUR_CERT_ID
```

```powershell
kubectl apply -f canvas3t-ingress-updated.yaml

# The ALB takes 2-3 minutes to provision
kubectl get ingress -n canvas3t -w
# NAME               CLASS    HOSTS             ADDRESS
# canvas3t-ingress   <none>   myart.run.place   canvas3t-alb-xxxxx.ap-south-1.elb.amazonaws.com
```

The ingress routes:
- `myart.run.place/api/*`   → backend service port 5000
- `myart.run.place/media/*` → backend service port 5000
- `myart.run.place/*`       → frontend service port 4173

Key annotations explained:
| Annotation | Value | Purpose |
|---|---|---|
| `alb.ingress.kubernetes.io/scheme` | `internet-facing` | Public ALB |
| `alb.ingress.kubernetes.io/target-type` | `ip` | Routes directly to pod IPs |
| `alb.ingress.kubernetes.io/listen-ports` | `HTTP:80, HTTPS:443` | Both protocols |
| `alb.ingress.kubernetes.io/healthcheck-path` | `/api/health` | ALB health check endpoint |
| `alb.ingress.kubernetes.io/success-codes` | `200` | Only 200 = healthy |

> **Critical:** The healthcheck-path must be `/api/health`. The backend has no route at `/`, so using the default `/` causes 404 → ALB marks target unhealthy → 503 for all requests.

---

## DNS & HTTPS Setup

### Point your domain to the ALB

Get the ALB DNS name:
```powershell
kubectl get ingress canvas3t-ingress -n canvas3t `
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

In your DNS provider (e.g. Route 53, Cloudflare):
- Create a **CNAME record**: `myart.run.place` → `canvas3t-alb-xxxxx.ap-south-1.elb.amazonaws.com`
- Or a **Route 53 A record (Alias)** pointing to the ALB

HTTPS works automatically once:
1. The ACM certificate status is **Issued**
2. The certificate ARN is set in the ingress annotation
3. DNS propagates (can take up to 48 hours but usually minutes)

### Verify HTTPS

```powershell
# Should return {"status": "ok"}
Invoke-WebRequest -Uri https://myart.run.place/api/health | Select-Object StatusCode, Content
```

---

## Verify Everything Works

```powershell
# 1. All pods running
kubectl get pods -n canvas3t

# 2. PVCs bound (should show Bound after first pod start)
kubectl get pvc -n canvas3t

# 3. ALB target health — BOTH targets must be healthy
$TG_ARN = (aws elbv2 describe-target-groups --region ap-south-1 `
  --query "TargetGroups[?contains(TargetGroupName,'canvas3t') && Port==\`5000\`].TargetGroupArn" `
  --output text)
aws elbv2 describe-target-health --target-group-arn $TG_ARN --region ap-south-1

# 4. Health endpoint
Invoke-WebRequest -Uri https://myart.run.place/api/health

# 5. Register a new user
$body = '{"username":"testuser","email":"test@example.com","password":"mypassword"}'
Invoke-WebRequest -Uri https://myart.run.place/api/auth/register `
  -Method POST -Body $body -ContentType "application/json"

# 6. Login
$body = '{"username":"testuser","password":"mypassword"}'
Invoke-WebRequest -Uri https://myart.run.place/api/auth/login `
  -Method POST -Body $body -ContentType "application/json"
```

---

## File Reference

| File | Purpose |
|---|---|
| `Dockerfile` | Backend image: Python 3.11-slim + gunicorn. Does **not** hardcode `IMAGE_DIR` or `DB_PATH` — those come from ConfigMap at runtime. |
| `frontend/Dockerfile` | Frontend multi-stage image: Stage 1 compiles Rust→WASM, Stage 2 runs npm install, Stage 3 runs Vite build, Stage 4 serves via Nginx. |
| `docker-compose.yml` | Local dev only. Backend on :5000, frontend on :5173. Uses named Docker volumes for DB and images. |
| `canvas3t-configmap.yaml` | All non-secret env vars for the backend pod. `DB_PATH=/data/db/app.db` and `IMAGE_DIR=/data/images` match the EBS mount points. |
| `canvas3t-secrets.yaml` | Template for the Kubernetes Secret. Fill in `SECRET_KEY` and apply once. **Never commit real values** — file is in `.gitignore`. |
| `canvas3t-storage.yaml` | `StorageClass` (EBS gp3, Retain policy) + two PVCs: 5Gi for SQLite, 20Gi for images. `reclaimPolicy: Retain` means data survives PVC deletion. |
| `canvas3t-backend-deployment.yaml` | Backend Deployment (1 replica, Recreate strategy) + ClusterIP Service. Mounts both PVCs. Probes hit `/api/health`. |
| `canvas3t-ingress-updated.yaml` | **Production ingress.** ALB with ACM HTTPS, health check on `/api/health`, routes `/api` and `/media` to backend, everything else to frontend. |
| `canvas3t-https.yaml` | Alternative ingress using nginx-ingress-controller + cert-manager for Let's Encrypt. Not used in production — kept as reference. |
| `alb-iam-policy.json` | IAM policy document for the AWS Load Balancer Controller service account. Apply once during cluster setup. |

---

## Troubleshooting

### 503 Service Unavailable on all API requests

The ALB health check is failing. Check the target group health:

```powershell
aws elbv2 describe-target-groups --region ap-south-1 `
  --query "TargetGroups[?contains(TargetGroupName,'canvas3t')].{Name:TargetGroupName,ARN:TargetGroupArn}" `
  --output table

# Fix: set health check to /api/health
aws elbv2 modify-target-group `
  --target-group-arn "YOUR_TARGET_GROUP_ARN" `
  --region ap-south-1 `
  --health-check-path "/api/health" `
  --matcher HttpCode=200
```

### Pod stuck in ContainerCreating

Usually means the EBS volume can't attach (already attached to another node):

```powershell
kubectl describe pod -n canvas3t -l app=canvas3t-backend
# Look for: "Unable to attach EBS volume"
# Fix: the Recreate strategy ensures only one pod at a time
# Wait 1-2 minutes for the old volume to detach
```

### Pod in CrashLoopBackOff

```powershell
# Check current logs
kubectl logs -n canvas3t deployment/canvas3t-backend

# Check previous crash logs
kubectl logs -n canvas3t deployment/canvas3t-backend --previous

# Common causes:
# - canvas3t-secrets does not exist → create it (Step 3)
# - DB_PATH directory not writable → check PVC is bound
```

### ECR image pull fails (ImagePullBackOff)

The ECR auth token expires every 12 hours:

```powershell
$REGION  = "ap-south-1"
$ACCOUNT = (aws sts get-caller-identity --query Account --output text)
$ECR_PASS = (aws ecr get-login-password --region $REGION)

# Delete and recreate the secret
kubectl delete secret ecr-secret -n canvas3t
kubectl create secret docker-registry ecr-secret `
  --docker-server="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com" `
  --docker-username=AWS `
  --docker-password=$ECR_PASS `
  -n canvas3t

kubectl rollout restart deployment/canvas3t-backend -n canvas3t
```

### 409 Conflict on registration

The username or email is already registered. Each username and email must be unique. Use a different username/email, or check existing users:

```powershell
kubectl exec -n canvas3t deployment/canvas3t-backend -- python -c "
from app import create_app
from app.models import User
app = create_app()
with app.app_context():
    for u in User.query.all():
        print(u.id, u.username, u.email)
"
```

### Images load slowly

The first request to a media file hits Flask's `send_from_directory`. For high traffic, consider adding a CloudFront distribution in front of the ALB and caching `/media/*`.

---

## Updating the Application

### Deploy new backend code

```powershell
$REGION  = "ap-south-1"
$ACCOUNT = (aws sts get-caller-identity --query Account --output text)
$ECR     = "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"

aws ecr get-login-password --region $REGION `
  | docker login --username AWS --password-stdin $ECR

docker build -f Dockerfile -t canvas3t-backend:latest .
docker tag canvas3t-backend:latest $ECR/canvas3t-backend:latest
docker push $ECR/canvas3t-backend:latest

kubectl rollout restart deployment/canvas3t-backend -n canvas3t
kubectl rollout status deployment/canvas3t-backend -n canvas3t
```

### Deploy new frontend code

```powershell
docker build -f frontend/Dockerfile -t canvas3t-frontend:latest .
docker tag canvas3t-frontend:latest $ECR/canvas3t-frontend:latest
docker push $ECR/canvas3t-frontend:latest

kubectl rollout restart deployment/canvas3t-frontend -n canvas3t
kubectl rollout status deployment/canvas3t-frontend -n canvas3t
```

### Roll back a bad deployment

```powershell
kubectl rollout undo deployment/canvas3t-backend -n canvas3t
kubectl rollout undo deployment/canvas3t-frontend -n canvas3t
```

### View live logs

```powershell
kubectl logs -n canvas3t deployment/canvas3t-backend --follow
kubectl logs -n canvas3t deployment/canvas3t-frontend --follow
```

### Scale replicas

The backend uses `Recreate` strategy and EBS `ReadWriteOnce` storage — it can only run as 1 replica. The frontend can scale freely:

```powershell
kubectl scale deployment canvas3t-frontend -n canvas3t --replicas=3
```

### Backup the database

```powershell
$POD = (kubectl get pod -n canvas3t -l app=canvas3t-backend -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n canvas3t $POD -- cp /data/db/app.db /data/db/app.db.bak
kubectl cp canvas3t/${POD}:/data/db/app.db ./app.db.backup
```
