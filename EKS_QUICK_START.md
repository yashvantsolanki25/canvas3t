# Canvas3T EKS Quick Start Guide

## 📋 Prerequisites Checklist

- [ ] AWS Account created
- [ ] AWS CLI v2 installed and configured (`aws configure`)
- [ ] kubectl installed
- [ ] Docker installed and running
- [ ] eksctl installed (optional but recommended)
- [ ] Git installed

## 🚀 Quickest Deployment Path (5-10 minutes)

### 1. Configure AWS (PowerShell)
```powershell
# Install tools (use Chocolatey)
choco install awscliv2 kubernetes-cli eksctl docker-desktop

# Configure credentials
aws configure
# Enter your AWS Access Key, Secret Key, region (us-east-1), and output format (json)

# Verify
aws sts get-caller-identity
```

### 2. Create EKS Cluster (15-20 minutes)
```powershell
eksctl create cluster `
  --name canvas3t-cluster `
  --region us-east-1 `
  --version 1.28 `
  --nodegroup-name canvas3t-nodes `
  --node-type t3.medium `
  --nodes 2 `
  --managed

# This automatically configures kubectl
kubectl get nodes  # Verify
```

### 3. Run Deployment Script (10 minutes)
```powershell
cd "c:\Users\Yashv\Downloads\Python_Flask\Python_Flask"

# Run the deployment script
.\kubernetes\deploy.ps1

# Script will:
# ✓ Create ECR repositories
# ✓ Build and push Docker images
# ✓ Create Kubernetes secrets
# ✓ Deploy all manifests
# ✓ Show you the ingress endpoint
```

### 4. Get Your Application URL
```powershell
# Get the ALB DNS name
kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Access your app
# Frontend: http://[ALB-DNS]
# Backend API: http://[ALB-DNS]/api
```

---

## 🔧 Manual Steps (If Script Doesn't Work)

### Create Repositories
```powershell
$REGION = "us-east-1"
aws ecr create-repository --repository-name canvas3t-backend --region $REGION
aws ecr create-repository --repository-name canvas3t-frontend --region $REGION
```

### Build and Push Images
```powershell
$AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$ECR_REGISTRY = "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Login
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build
docker build -f Dockerfile -t canvas3t-backend:latest .
docker build -f frontend/Dockerfile -t canvas3t-frontend:latest .

# Tag
docker tag canvas3t-backend:latest "$ECR_REGISTRY/canvas3t-backend:latest"
docker tag canvas3t-frontend:latest "$ECR_REGISTRY/canvas3t-frontend:latest"

# Push
docker push "$ECR_REGISTRY/canvas3t-backend:latest"
docker push "$ECR_REGISTRY/canvas3t-frontend:latest"
```

### Update YAML Files
Before deploying, edit these files:
- `kubernetes/02-backend-deployment.yaml` - Replace `YOUR_AWS_ACCOUNT_ID`
- `kubernetes/03-frontend-deployment.yaml` - Replace `YOUR_AWS_ACCOUNT_ID` and update `VITE_API_URL`
- `kubernetes/04-ingress-network.yaml` - Replace `yourdomain.com` with your domain

### Deploy
```powershell
kubectl apply -f kubernetes/00-namespace-config.yaml
kubectl apply -f kubernetes/01-storage.yaml
kubectl apply -f kubernetes/02-backend-deployment.yaml
kubectl apply -f kubernetes/03-frontend-deployment.yaml
kubectl apply -f kubernetes/04-ingress-network.yaml
kubectl apply -f kubernetes/05-hpa.yaml

# Wait for rollout
kubectl rollout status deployment/canvas3t-backend -n canvas3t
kubectl rollout status deployment/canvas3t-frontend -n canvas3t
```

---

## 📊 Monitoring Commands

```powershell
# Check all resources
kubectl get all -n canvas3t

# View logs
kubectl logs -f deployment/canvas3t-backend -n canvas3t
kubectl logs -f deployment/canvas3t-frontend -n canvas3t

# Port forward to access locally
kubectl port-forward svc/canvas3t-backend 5000:5000 -n canvas3t
# http://localhost:5000/api/health

# Check resource usage
kubectl top pods -n canvas3t

# Describe issues
kubectl describe pod <pod-name> -n canvas3t

# Get all events
kubectl get events -n canvas3t
```

---

## 🛠️ Troubleshooting

### Pods not starting?
```powershell
kubectl describe pod <pod-name> -n canvas3t
kubectl logs <pod-name> -n canvas3t
```

### Image pull errors?
```powershell
# Check ECR secret
kubectl get secrets -n canvas3t

# Verify ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com
```

### Health check failures?
```powershell
# SSH into pod and test
kubectl exec -it <pod-name> -n canvas3t -- /bin/bash
curl http://localhost:5000/api/health
```

### Ingress not showing IP?
```powershell
# Wait for ALB to provision (can take 2-3 minutes)
kubectl get ingress canvas3t-ingress -n canvas3t -w

# Check ALB controller
kubectl logs -l app.kubernetes.io/name=aws-load-balancer-controller -n kube-system
```

---

## 💰 Cost Optimization

1. **Use Spot Instances** - Add `--spot` to eksctl command (70% savings)
2. **Right-size instances** - Start with t3.medium, scale based on usage
3. **Set resource limits** - Already configured in manifests
4. **Use autoscaling** - Already enabled with HPA
5. **Delete unused resources** - Clean up when done

---

## 🗑️ Cleanup (When Done Testing)

```powershell
# Delete namespace and all resources
kubectl delete namespace canvas3t

# Delete EKS cluster
eksctl delete cluster --name canvas3t-cluster --region us-east-1

# Delete ECR repositories
aws ecr delete-repository --repository-name canvas3t-backend --force --region us-east-1
aws ecr delete-repository --repository-name canvas3t-frontend --force --region us-east-1
```

---

## ✅ Deployment Checklist

- [ ] AWS credentials configured
- [ ] EKS cluster created
- [ ] ECR repositories created
- [ ] Docker images built and pushed
- [ ] Kubernetes manifests updated with actual values
- [ ] Secrets created for sensitive data
- [ ] Deployments applied and ready
- [ ] Ingress created and ALB provisioned
- [ ] DNS records updated (if using custom domain)
- [ ] Application accessible via ingress
- [ ] Health checks passing
- [ ] Logs monitoring configured
- [ ] Auto-scaling enabled

---

## 📚 Useful Resources

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [eksctl Documentation](https://eksctl.io/)
- [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [ALB Ingress Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)

---

## 🆘 Support & Next Steps

1. Review `EKS_DEPLOYMENT_GUIDE.md` for detailed information
2. Check `kubernetes/` directory for all manifests
3. Run `.\kubernetes\deploy.ps1` for automated deployment
4. Monitor with `kubectl logs` and `kubectl describe`
5. Scale and update as needed with kubectl commands

**Questions?** Check the troubleshooting section or AWS documentation!
