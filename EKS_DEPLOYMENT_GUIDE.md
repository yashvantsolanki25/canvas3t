# AWS EKS Deployment Guide for Canvas3T Application

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS Setup](#aws-setup)
3. [Build and Push Images to ECR](#build-and-push-images-to-ecr)
4. [Create EKS Cluster](#create-eks-cluster)
5. [Deploy Application to EKS](#deploy-application-to-eks)
6. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Prerequisites

### Required Tools
- AWS CLI v2+ configured with credentials
- kubectl (Kubernetes CLI)
- Docker
- helm (optional, for advanced deployments)
- eksctl (AWS EKS CLI tool - simplifies cluster creation)

### Installation on Windows (PowerShell)

```powershell
# Install AWS CLI v2
# Download from: https://awsclip.amazonaws.com/AWSCLIV2.msi
# Or use chocolatey:
choco install awscliv2

# Install kubectl
choco install kubernetes-cli

# Install eksctl
choco install eksctl

# Install Docker Desktop (if not already installed)
choco install docker-desktop

# Verify installations
aws --version
kubectl version --client
eksctl version
docker --version
```

### AWS Account Requirements
- AWS Account with appropriate permissions
- IAM user with EC2, ECR, EKS, IAM permissions
- Default VPC or custom VPC ready
- AWS region selected (e.g., `us-east-1`)

---

## AWS Setup

### Step 1: Configure AWS Credentials

```powershell
# Configure AWS CLI
aws configure

# When prompted, enter:
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### Step 2: Create ECR Repositories

```powershell
# Set variables
$REGION = "us-east-1"
$AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$ECR_REGISTRY = "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Create ECR repositories
aws ecr create-repository `
  --repository-name canvas3t-backend `
  --region $REGION `
  --image-scanning-configuration scanOnPush=true `
  --image-tag-mutability MUTABLE

aws ecr create-repository `
  --repository-name canvas3t-frontend `
  --region $REGION `
  --image-scanning-configuration scanOnPush=true `
  --image-tag-mutability MUTABLE

# Output ECR URLs
Write-Host "Backend ECR URL: $ECR_REGISTRY/canvas3t-backend"
Write-Host "Frontend ECR URL: $ECR_REGISTRY/canvas3t-frontend"
```

### Step 3: Create IAM Role for EKS Nodes

```powershell
# Create IAM role for EKS worker nodes
aws iam create-role `
  --role-name canvas3t-eks-nodegroup-role `
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "ec2.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Attach required policies
aws iam attach-role-policy `
  --role-name canvas3t-eks-nodegroup-role `
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy

aws iam attach-role-policy `
  --role-name canvas3t-eks-nodegroup-role `
  --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy

aws iam attach-role-policy `
  --role-name canvas3t-eks-nodegroup-role `
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

# Create EKS cluster role
aws iam create-role `
  --role-name canvas3t-eks-cluster-role `
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "eks.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

aws iam attach-role-policy `
  --role-name canvas3t-eks-cluster-role `
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy
```

---

## Build and Push Images to ECR

### Step 1: Login to ECR

```powershell
$REGION = "us-east-1"
$AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$ECR_REGISTRY = "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Get login token and login to Docker
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

Write-Host "Successfully logged into ECR"
```

### Step 2: Build Backend Image

```powershell
# Navigate to project root
cd "c:\Users\Yashv\Downloads\Python_Flask\Python_Flask"

# Build backend image
docker build -f Dockerfile -t canvas3t-backend:latest .

# Tag for ECR
docker tag canvas3t-backend:latest "$ECR_REGISTRY/canvas3t-backend:latest"
docker tag canvas3t-backend:latest "$ECR_REGISTRY/canvas3t-backend:v1.0.0"

# Push to ECR
docker push "$ECR_REGISTRY/canvas3t-backend:latest"
docker push "$ECR_REGISTRY/canvas3t-backend:v1.0.0"

Write-Host "Backend image pushed to ECR"
```

### Step 3: Build Frontend Image

```powershell
# Build frontend image
docker build -f frontend/Dockerfile -t canvas3t-frontend:latest . --build-arg VITE_API_URL=https://api.yourdomain.com

# Tag for ECR
docker tag canvas3t-frontend:latest "$ECR_REGISTRY/canvas3t-frontend:latest"
docker tag canvas3t-frontend:latest "$ECR_REGISTRY/canvas3t-frontend:v1.0.0"

# Push to ECR
docker push "$ECR_REGISTRY/canvas3t-frontend:latest"
docker push "$ECR_REGISTRY/canvas3t-frontend:v1.0.0"

Write-Host "Frontend image pushed to ECR"
```

### Step 4: Verify Images in ECR

```powershell
# List backend images
aws ecr describe-images --repository-name canvas3t-backend --region $REGION

# List frontend images
aws ecr describe-images --repository-name canvas3t-frontend --region $REGION
```

---

## Create EKS Cluster

### Option A: Using eksctl (Recommended - Simplest)

```powershell
# Create EKS cluster with one command
eksctl create cluster `
  --name canvas3t-cluster `
  --region us-east-1 `
  --version 1.28 `
  --nodegroup-name canvas3t-nodes `
  --node-type t3.medium `
  --nodes 2 `
  --nodes-min 1 `
  --nodes-max 4 `
  --managed

# This takes ~15-20 minutes. Wait for completion.
# kubectl context is automatically configured.

# Verify cluster
kubectl get nodes
kubectl get pods -A
```

### Option B: Using AWS CLI (More Control)

```powershell
$CLUSTER_NAME = "canvas3t-cluster"
$REGION = "us-east-1"

# Create cluster
aws eks create-cluster `
  --name $CLUSTER_NAME `
  --version 1.28 `
  --role-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/canvas3t-eks-cluster-role" `
  --resources-vpc-config subnetIds=subnet-xxxxx,subnet-xxxxx `
  --region $REGION

# Wait for cluster to be ACTIVE (5-10 minutes)
aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.status'

# Update kubeconfig
aws eks update-kubeconfig --name $CLUSTER_NAME --region $REGION

# Create node group
aws eks create-nodegroup `
  --cluster-name $CLUSTER_NAME `
  --nodegroup-name canvas3t-nodes `
  --subnets subnet-xxxxx subnet-xxxxx `
  --node-role "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/canvas3t-eks-nodegroup-role" `
  --scaling-config minSize=1,maxSize=4,desiredSize=2 `
  --instance-types t3.medium `
  --region $REGION

# Wait for node group to be ACTIVE
aws eks describe-nodegroup `
  --cluster-name $CLUSTER_NAME `
  --nodegroup-name canvas3t-nodes `
  --region $REGION `
  --query 'nodegroup.status'
```

### Verify Cluster Setup

```powershell
# Check nodes
kubectl get nodes

# Check kube-system pods
kubectl get pods -n kube-system

# Check cluster info
kubectl cluster-info
```

---

## Deploy Application to EKS

### Step 1: Create Kubernetes Namespace

```powershell
kubectl create namespace canvas3t
kubectl label namespace canvas3t environment=production
```

### Step 2: Create Secrets for Database and Configuration

```powershell
# Create secret for Flask configuration
kubectl create secret generic canvas3t-secrets `
  --from-literal=SECRET_KEY="your-super-secret-key-change-this" `
  --from-literal=DB_PASSWORD="your-db-password" `
  -n canvas3t

# Create ConfigMap for application configuration
kubectl create configmap canvas3t-config `
  --from-literal=FLASK_ENV="production" `
  --from-literal=RESULTS_PER_PAGE="24" `
  --from-literal=IMAGE_DIR="/app/images" `
  --from-literal=DB_PATH="/app/db/app.db" `
  -n canvas3t

# Verify
kubectl get secrets -n canvas3t
kubectl get configmaps -n canvas3t
```

### Step 3: Create Persistent Volumes (for database and images)

**Create file: `kubernetes/pvc.yaml`**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: canvas3t-db-pvc
  namespace: canvas3t
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp2  # EBS backed storage
  resources:
    requests:
      storage: 10Gi

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: canvas3t-images-pvc
  namespace: canvas3t
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp2
  resources:
    requests:
      storage: 50Gi  # Adjust based on your image storage needs
```

Apply the manifest:
```powershell
kubectl apply -f kubernetes/pvc.yaml
kubectl get pvc -n canvas3t
```

### Step 4: Create Backend Deployment

**Create file: `kubernetes/backend-deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: canvas3t-backend
  namespace: canvas3t
  labels:
    app: canvas3t-backend
    version: v1
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: canvas3t-backend
  template:
    metadata:
      labels:
        app: canvas3t-backend
        version: v1
    spec:
      containers:
      - name: backend
        image: YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/canvas3t-backend:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
          name: http
        
        env:
        - name: FLASK_APP
          value: "app"
        - name: FLASK_ENV
          valueFrom:
            configMapKeyRef:
              name: canvas3t-config
              key: FLASK_ENV
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: canvas3t-secrets
              key: SECRET_KEY
        - name: IMAGE_DIR
          valueFrom:
            configMapKeyRef:
              name: canvas3t-config
              key: IMAGE_DIR
        - name: DB_PATH
          valueFrom:
            configMapKeyRef:
              name: canvas3t-config
              key: DB_PATH
        - name: RESULTS_PER_PAGE
          valueFrom:
            configMapKeyRef:
              name: canvas3t-config
              key: RESULTS_PER_PAGE
        
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        
        livenessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        
        volumeMounts:
        - name: images
          mountPath: /app/images
        - name: db
          mountPath: /app/db
      
      volumes:
      - name: images
        persistentVolumeClaim:
          claimName: canvas3t-images-pvc
      - name: db
        persistentVolumeClaim:
          claimName: canvas3t-db-pvc
      
      imagePullSecrets:
      - name: ecr-secret

---
apiVersion: v1
kind: Service
metadata:
  name: canvas3t-backend
  namespace: canvas3t
  labels:
    app: canvas3t-backend
spec:
  type: ClusterIP
  ports:
  - port: 5000
    targetPort: 5000
    protocol: TCP
    name: http
  selector:
    app: canvas3t-backend
```

### Step 5: Create Frontend Deployment

**Create file: `kubernetes/frontend-deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: canvas3t-frontend
  namespace: canvas3t
  labels:
    app: canvas3t-frontend
    version: v1
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: canvas3t-frontend
  template:
    metadata:
      labels:
        app: canvas3t-frontend
        version: v1
    spec:
      containers:
      - name: frontend
        image: YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/canvas3t-frontend:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 4173
          name: http
        
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "250m"
        
        livenessProbe:
          httpGet:
            path: /
            port: 4173
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /
            port: 4173
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2

---
apiVersion: v1
kind: Service
metadata:
  name: canvas3t-frontend
  namespace: canvas3t
  labels:
    app: canvas3t-frontend
spec:
  type: ClusterIP
  ports:
  - port: 4173
    targetPort: 4173
    protocol: TCP
    name: http
  selector:
    app: canvas3t-frontend
```

### Step 6: Create Ingress for External Access

**Create file: `kubernetes/ingress.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: canvas3t-ingress
  namespace: canvas3t
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - yourdomain.com
    - www.yourdomain.com
    secretName: canvas3t-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: canvas3t-frontend
            port:
              number: 4173
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: canvas3t-backend
            port:
              number: 5000
  - host: www.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: canvas3t-frontend
            port:
              number: 4173
```

### Step 7: Create ECR Secret for Image Pull

```powershell
# Get ECR login credentials
$ECR_LOGIN = aws ecr get-login-password --region us-east-1
$AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)

# Create secret for ECR authentication
kubectl create secret docker-registry ecr-secret `
  --docker-server="$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com" `
  --docker-username=AWS `
  --docker-password=$ECR_LOGIN `
  -n canvas3t

# Verify
kubectl get secrets -n canvas3t
```

### Step 8: Deploy All Resources

```powershell
# Update image URLs in YAML files first!
# Replace "YOUR_AWS_ACCOUNT_ID" with actual account ID:
$AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
Write-Host "Use this Account ID in your YAML files: $AWS_ACCOUNT_ID"

# Create kubernetes directory if it doesn't exist
mkdir -p kubernetes

# Apply all manifests
kubectl apply -f kubernetes/pvc.yaml
kubectl apply -f kubernetes/backend-deployment.yaml
kubectl apply -f kubernetes/frontend-deployment.yaml
kubectl apply -f kubernetes/ingress.yaml

# Verify deployments
kubectl get deployments -n canvas3t
kubectl get pods -n canvas3t
kubectl get svc -n canvas3t
kubectl get ingress -n canvas3t

# Watch pod startup
kubectl get pods -n canvas3t -w
```

---

## Monitoring & Maintenance

### View Logs

```powershell
# Backend logs
kubectl logs -n canvas3t deployment/canvas3t-backend -f

# Frontend logs
kubectl logs -n canvas3t deployment/canvas3t-frontend -f

# Specific pod logs
kubectl logs -n canvas3t pod/canvas3t-backend-xxxxx -c backend
```

### Access Application

```powershell
# Port forward to access locally
kubectl port-forward -n canvas3t svc/canvas3t-backend 5000:5000
kubectl port-forward -n canvas3t svc/canvas3t-frontend 4173:4173

# Then access:
# Backend: http://localhost:5000
# Frontend: http://localhost:4173
```

### Scale Deployments

```powershell
# Scale backend to 3 replicas
kubectl scale deployment canvas3t-backend -n canvas3t --replicas=3

# Scale frontend to 2 replicas
kubectl scale deployment canvas3t-frontend -n canvas3t --replicas=2

# Check scaling
kubectl get pods -n canvas3t
```

### Rolling Update with New Image

```powershell
# Update backend image
kubectl set image deployment/canvas3t-backend `
  backend=YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/canvas3t-backend:v1.1.0 `
  -n canvas3t

# Check rollout status
kubectl rollout status deployment/canvas3t-backend -n canvas3t

# Rollback if needed
kubectl rollout undo deployment/canvas3t-backend -n canvas3t
```

### Monitor Resource Usage

```powershell
# Install metrics-server (if not already installed)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# View resource usage
kubectl top nodes
kubectl top pods -n canvas3t
```

### Database Backup

```powershell
# Copy database from PVC to local
kubectl exec -n canvas3t -it canvas3t-backend-xxxxx -- /bin/bash
# Inside pod: tar -czf /tmp/db-backup.tar.gz /app/db
kubectl cp canvas3t/canvas3t-backend-xxxxx:/tmp/db-backup.tar.gz ./db-backup.tar.gz
```

### Cleanup (if needed)

```powershell
# Delete namespace (removes all resources)
kubectl delete namespace canvas3t

# Delete cluster
eksctl delete cluster --name canvas3t-cluster --region us-east-1
```

---

## Troubleshooting

### Pods not starting
```powershell
kubectl describe pod canvas3t-backend-xxxxx -n canvas3t
kubectl logs canvas3t-backend-xxxxx -n canvas3t
```

### Image pull errors
```powershell
# Check ECR secret
kubectl get secrets ecr-secret -n canvas3t

# Check pod events
kubectl describe pod canvas3t-backend-xxxxx -n canvas3t
```

### Database connection issues
```powershell
# Verify PVC is mounted
kubectl describe pod canvas3t-backend-xxxxx -n canvas3t

# Check PVC status
kubectl get pvc -n canvas3t
```

### Health check failures
```powershell
# Test endpoint from pod
kubectl exec -n canvas3t -it canvas3t-backend-xxxxx -- curl http://localhost:5000/api/health
```

---

## Cost Optimization Tips

1. **Use Spot Instances**: Add `--spot` flag to eksctl for 70% cost savings
2. **Right-size instances**: Start with t3.medium and adjust based on metrics
3. **Use Cluster Autoscaler**: Auto-scale nodes based on demand
4. **Set resource limits**: Prevents resource waste
5. **Regular cleanup**: Delete unused resources

---

## Next Steps

1. Replace placeholder values (AWS Account ID, domain names, secrets)
2. Create Kubernetes manifests in `kubernetes/` directory
3. Test locally: `docker-compose up`
4. Push images to ECR
5. Create and verify EKS cluster
6. Deploy application
7. Monitor and optimize

**Good luck with your deployment! 🚀**
