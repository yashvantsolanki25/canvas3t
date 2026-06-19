# 🎯 Canvas3T EKS Deployment - Quick Reference Card

## 📋 Files Created For You

```
c:\Users\Yashv\Downloads\Python_Flask\Python_Flask\
├── DEPLOYMENT_DOCUMENTATION_INDEX.md (START HERE!)
├── EKS_QUICK_START.md (Fastest setup - 5-10 min)
├── EKS_DEPLOYMENT_GUIDE.md (Complete guide)
├── KUBERNETES_COMMANDS_REFERENCE.md (kubectl commands)
├── PRODUCTION_DEPLOYMENT.md (Production setup)
├── POST_DEPLOYMENT_VERIFICATION.md (Verification checklist)
└── kubernetes/
    ├── deploy.ps1 (Automated deployment - Windows)
    ├── deploy.sh (Automated deployment - Linux)
    ├── setup-infrastructure.ps1 (Create infrastructure)
    ├── 00-namespace-config.yaml
    ├── 01-storage.yaml
    ├── 02-backend-deployment.yaml
    ├── 03-frontend-deployment.yaml
    ├── 04-ingress-network.yaml
    └── 05-hpa.yaml
```

---

## ⚡ 3-Step Super Quick Deployment (Windows PowerShell)

### Step 1: Prerequisites (5 minutes)
```powershell
# Install tools
choco install awscliv2 kubernetes-cli eksctl docker-desktop

# Configure AWS
aws configure
# Enter: Access Key, Secret Key, region (us-east-1), output (json)

# Verify
aws sts get-caller-identity
```

### Step 2: Create EKS Cluster (20 minutes)
```powershell
eksctl create cluster `
  --name canvas3t-cluster `
  --region us-east-1 `
  --version 1.28 `
  --nodegroup-name canvas3t-nodes `
  --node-type t3.medium `
  --nodes 2 `
  --managed
```

### Step 3: Deploy Application (10 minutes)
```powershell
cd "c:\Users\Yashv\Downloads\Python_Flask\Python_Flask"
.\kubernetes\deploy.ps1
```

**Done! Your app is live!** 🎉

---

## 🔑 Important: Pre-Deployment Updates

Before running deploy.ps1, update these files:

### 1. Get your AWS Account ID
```powershell
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
Write-Host $ACCOUNT_ID
```

### 2. Update Kubernetes Manifests
Find and replace in `kubernetes/*.yaml`:
- `YOUR_AWS_ACCOUNT_ID` → Your actual AWS Account ID
- `yourdomain.com` → Your actual domain (or ALB DNS later)

### 3. Update Secrets
Edit `kubernetes/00-namespace-config.yaml`:
```yaml
SECRET_KEY: "canvas3t-production-secret-key-please-change-this-to-something-secure"
```
Change to a strong random value!

---

## 📊 Key Commands Cheat Sheet

### Cluster Info
```powershell
kubectl cluster-info                           # Cluster details
kubectl get nodes                              # List nodes
kubectl get nodes -o wide                      # Detailed node info
```

### Deployment Status
```powershell
kubectl get pods -n canvas3t                   # List all pods
kubectl get deployment -n canvas3t             # List deployments
kubectl get svc -n canvas3t                    # List services
kubectl get ingress -n canvas3t                # List ingress
```

### Access Application
```powershell
# Get ALB endpoint
kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Access via port forward
kubectl port-forward svc/canvas3t-backend 5000:5000 -n canvas3t
kubectl port-forward svc/canvas3t-frontend 4173:4173 -n canvas3t
```

### Monitoring
```powershell
kubectl logs -f deployment/canvas3t-backend -n canvas3t           # Live logs
kubectl top pods -n canvas3t                                      # Resource usage
kubectl describe pod <pod-name> -n canvas3t                       # Pod details
kubectl get events -n canvas3t --sort-by='.lastTimestamp'        # Recent events
```

### Scaling
```powershell
kubectl scale deployment canvas3t-backend --replicas=3 -n canvas3t
kubectl autoscale deployment canvas3t-backend --min=2 --max=10 -n canvas3t
```

### Updating Images
```powershell
kubectl set image deployment/canvas3t-backend `
  backend=YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/canvas3t-backend:v1.1.0 `
  -n canvas3t
```

### Troubleshooting
```powershell
kubectl describe pod <pod-name> -n canvas3t          # Check errors
kubectl logs <pod-name> -n canvas3t --previous       # Previous logs
kubectl exec -it <pod-name> -n canvas3t -- bash      # SSH into pod
kubectl delete pod <pod-name> -n canvas3t            # Restart pod
```

---

## 🔐 Security Checklist

- [ ] Changed SECRET_KEY to strong random value
- [ ] Updated FLASK_ENV to "production"
- [ ] Configured HTTPS with ACM certificate
- [ ] Set up VPC security groups
- [ ] Enabled network policies
- [ ] Set up CloudWatch logging
- [ ] Configured backup strategy
- [ ] Limited pod resource usage

---

## 💰 Cost Breakdown (Monthly Estimate)

| Component | Hourly | Monthly |
|-----------|--------|---------|
| EKS Cluster | $0.10 | $73 |
| 2 x t3.medium | $0.052 | $76 |
| ALB | ~$0.50 | $16 |
| Data Transfer | Variable | ~$10 |
| **Total** | ~**$0.65** | ~**$175** |

**Cost Optimization**: Use Spot Instances for 70% savings!

---

## 🚨 Troubleshooting Quick Fixes

### Problem: "Unable to connect to the server"
```powershell
aws eks update-kubeconfig --name canvas3t-cluster --region us-east-1
```

### Problem: "ImagePullBackOff"
```powershell
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com
```

### Problem: Pods stuck in "Pending"
```powershell
kubectl describe node <node-name>              # Check resources
kubectl get events -n canvas3t                 # Check events
```

### Problem: Health check failing
```powershell
kubectl exec -it <pod-name> -n canvas3t -- curl http://localhost:5000/api/health
```

### Problem: ALB endpoint shows <pending>
```powershell
kubectl describe ingress canvas3t-ingress -n canvas3t  # Check status
# Wait 2-3 minutes for ALB to provision
```

---

## 📞 Documentation Map

| Need | File | Time |
|------|------|------|
| **Start here** | DEPLOYMENT_DOCUMENTATION_INDEX.md | 5 min |
| **Quick setup** | EKS_QUICK_START.md | 10 min |
| **Detailed guide** | EKS_DEPLOYMENT_GUIDE.md | 30 min |
| **kubectl commands** | KUBERNETES_COMMANDS_REFERENCE.md | Reference |
| **Production setup** | PRODUCTION_DEPLOYMENT.md | 1 hour |
| **Verify deployment** | POST_DEPLOYMENT_VERIFICATION.md | 20 min |

---

## ✅ Verification Checklist

After deployment, verify:

```powershell
# 1. Cluster is running
kubectl get nodes

# 2. All pods are running
kubectl get pods -n canvas3t

# 3. Services have endpoints
kubectl get svc -n canvas3t

# 4. Ingress has ALB endpoint
kubectl get ingress canvas3t-ingress -n canvas3t

# 5. Can access frontend
curl http://$(kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# 6. Can access backend API
curl http://$(kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')/api/health

# 7. Health check passes
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- curl http://localhost:5000/api/health
```

✅ = Deployment successful!

---

## 🔄 Day-to-Day Operations

### Monitor Application
```powershell
# Watch logs
kubectl logs -f deployment/canvas3t-backend -n canvas3t

# Watch pod status
kubectl get pods -n canvas3t -w

# Monitor resources
kubectl top pods -n canvas3t
```

### Deploy New Version
```powershell
# Build and push new image
docker build -f Dockerfile -t canvas3t-backend:v1.1.0 .
docker tag canvas3t-backend:v1.1.0 $ECR_REGISTRY/canvas3t-backend:v1.1.0
docker push $ECR_REGISTRY/canvas3t-backend:v1.1.0

# Update deployment
kubectl set image deployment/canvas3t-backend backend=$ECR_REGISTRY/canvas3t-backend:v1.1.0 -n canvas3t

# Check rollout
kubectl rollout status deployment/canvas3t-backend -n canvas3t
```

### Scale Application
```powershell
# Manual scaling
kubectl scale deployment canvas3t-backend --replicas=3 -n canvas3t

# Check HPA
kubectl get hpa -n canvas3t

# Describe HPA to see current metrics
kubectl describe hpa canvas3t-backend-hpa -n canvas3t
```

### Backup Database
```powershell
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- tar -czf /tmp/db-backup.tar.gz /app/db
kubectl cp canvas3t/canvas3t-backend-xxxxx:/tmp/db-backup.tar.gz ./db-backup.tar.gz
```

---

## 🎯 Success Indicators

Your deployment is successful when:

✅ Cluster has all nodes in "Ready" state
✅ All pods in canvas3t namespace are "Running"  
✅ All services have Endpoints  
✅ Ingress has ALB endpoint assigned
✅ Frontend accessible via ALB DNS
✅ Backend API returns health check response
✅ Database file exists and has data
✅ Images are persisted in PVC
✅ Logs are collectible
✅ Application loads in browser

---

## 🆘 Getting Help

1. **Check logs**: `kubectl logs -f deployment/canvas3t-backend -n canvas3t`
2. **Describe pod**: `kubectl describe pod <name> -n canvas3t`
3. **Check events**: `kubectl get events -n canvas3t`
4. **Read guides**:
   - [KUBERNETES_COMMANDS_REFERENCE.md](KUBERNETES_COMMANDS_REFERENCE.md)
   - [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
5. **AWS Docs**: https://docs.aws.amazon.com/eks/

---

## 📚 Useful Links

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Official Docs](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)

---

## 🚀 Next Steps

1. ✅ Install prerequisites
2. ✅ Create EKS cluster
3. ✅ Update configuration files
4. ✅ Run deploy.ps1
5. ✅ Verify deployment
6. ✅ Set up monitoring
7. ✅ Configure backups
8. ✅ Go live! 🎉

---

**Created**: 2026-06-18  
**Last Updated**: 2026-06-18  
**Version**: 1.0

Print this card and keep it handy! 📌
