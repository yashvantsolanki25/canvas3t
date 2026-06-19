# 📚 Canvas3T EKS Deployment - Complete Documentation Index

## 📖 Documentation Files

Your complete EKS deployment guide consists of the following documents:

### 1. **[EKS_QUICK_START.md](EKS_QUICK_START.md)** ⚡
**Start here!** Quick 5-10 minute setup guide with simplified steps.
- Prerequisites checklist
- Fastest deployment path using eksctl
- Common troubleshooting issues
- Cost optimization tips

### 2. **[EKS_DEPLOYMENT_GUIDE.md](EKS_DEPLOYMENT_GUIDE.md)** 📋
Comprehensive deployment guide with detailed explanations.
- Complete prerequisites setup
- AWS account configuration
- ECR repository creation
- EKS cluster creation (both eksctl and AWS CLI methods)
- Kubernetes manifest explanation
- Monitoring and maintenance commands

### 3. **[KUBERNETES_COMMANDS_REFERENCE.md](KUBERNETES_COMMANDS_REFERENCE.md)** 🔧
Quick reference for common kubectl commands.
- Deployment status checks
- Logging and monitoring
- Scaling operations
- Port forwarding
- Troubleshooting commands
- Emergency procedures

### 4. **[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)** 🚀
Production-ready best practices and security configurations.
- Pre-deployment checklist
- Security hardening
- Monitoring setup (Prometheus, CloudWatch)
- Backup and disaster recovery
- Performance tuning
- Production troubleshooting guide

---

## 📁 Kubernetes Manifests Directory

Location: `kubernetes/`

### Configuration Files (in order):
1. **`00-namespace-config.yaml`** - Namespace, ConfigMaps, Secrets
2. **`01-storage.yaml`** - Storage Classes, PVCs
3. **`02-backend-deployment.yaml`** - Backend deployment and service
4. **`03-frontend-deployment.yaml`** - Frontend deployment and service
5. **`04-ingress-network.yaml`** - Ingress and network policies
6. **`05-hpa.yaml`** - Horizontal Pod Autoscaler

### Deployment Scripts:
- **`deploy.ps1`** - PowerShell deployment script (Windows) ⭐
- **`deploy.sh`** - Bash deployment script (Linux/Mac)
- **`setup-infrastructure.ps1`** - AWS infrastructure setup script

---

## 🚀 Getting Started - 3 Approaches

### Approach 1: Fastest (Recommended for Beginners) ⚡
```powershell
# 1. Read this file first:
# EKS_QUICK_START.md

# 2. Run one-command cluster setup:
eksctl create cluster --name canvas3t-cluster --region us-east-1 --version 1.28 --nodegroup-name canvas3t-nodes --node-type t3.medium --nodes 2 --managed

# 3. Run automated deployment:
cd "c:\Users\Yashv\Downloads\Python_Flask\Python_Flask"
.\kubernetes\deploy.ps1

# 4. Done! Your app is live
```

### Approach 2: Step-by-Step (For Learning) 📖
```powershell
# Follow all steps in:
# EKS_DEPLOYMENT_GUIDE.md

# This takes longer but you understand each component
```

### Approach 3: Infrastructure as Code (For Production) 🏢
```powershell
# Use the infrastructure setup script:
.\kubernetes\setup-infrastructure.ps1

# Then apply manifests manually:
kubectl apply -f kubernetes/
```

---

## ⏱️ Timeline Estimate

| Step | Duration | Command |
|------|----------|---------|
| Prerequisites setup | 10 min | `aws configure` + install tools |
| EKS cluster creation | 15-20 min | `eksctl create cluster ...` |
| Build Docker images | 5-10 min | `docker build` |
| Push to ECR | 3-5 min | `docker push` |
| Deploy to EKS | 2-3 min | `kubectl apply` |
| ALB provisioning | 2-3 min | *automatic* |
| **Total** | **~40-50 min** | |

---

## 🎯 Quick Command Reference

### Initial Setup
```powershell
# Install prerequisites
choco install awscliv2 kubernetes-cli eksctl docker-desktop

# Configure AWS
aws configure

# Verify credentials
aws sts get-caller-identity
```

### Create Infrastructure
```powershell
# Option A: Automatic (recommended)
eksctl create cluster --name canvas3t-cluster --region us-east-1 --version 1.28 --nodegroup-name canvas3t-nodes --node-type t3.medium --nodes 2 --managed

# Option B: Using script
.\kubernetes\setup-infrastructure.ps1
```

### Deploy Application
```powershell
# Update kubeconfig
aws eks update-kubeconfig --name canvas3t-cluster --region us-east-1

# Run deployment script
.\kubernetes\deploy.ps1
```

### Get Application URL
```powershell
kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### Monitor Application
```powershell
# View logs
kubectl logs -f deployment/canvas3t-backend -n canvas3t

# Check pod status
kubectl get pods -n canvas3t

# Port forward for local testing
kubectl port-forward svc/canvas3t-backend 5000:5000 -n canvas3t
```

---

## ⚠️ Important Before You Start

### 1. Update Configuration Files
- Replace `YOUR_AWS_ACCOUNT_ID` with your actual AWS Account ID
- Replace `yourdomain.com` with your actual domain
- Update `SECRET_KEY` to a strong random value

### 2. AWS Account Requirements
- Valid AWS account with billing enabled
- IAM user with EC2, ECR, EKS, IAM permissions
- Sufficient service quotas (EC2 instances, ELBs, etc.)

### 3. Costs
- **EKS Cluster**: $0.10/hour (~$73/month)
- **EC2 Nodes (2 x t3.medium)**: ~$0.052/hour each
- **ALB**: ~$16/month
- **Data Transfer**: ~$0.02/GB
- **Estimated Monthly Cost**: $150-200 for minimal setup

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    AWS Account (us-east-1)              │
│  ┌───────────────────────────────────────────────────┐  │
│  │                  EKS Cluster                      │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │              Kubernetes Control Plane       │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  │                                                     │  │
│  │  ┌──────────────────┐  ┌──────────────────┐      │  │
│  │  │  Worker Node 1   │  │  Worker Node 2   │      │  │
│  │  │  ┌────────────┐  │  │  ┌────────────┐  │      │  │
│  │  │  │  Backend   │  │  │  │  Backend   │  │      │  │
│  │  │  │  Pod       │  │  │  │  Pod       │  │      │  │
│  │  │  └────────────┘  │  │  └────────────┘  │      │  │
│  │  │  ┌────────────┐  │  │  ┌────────────┐  │      │  │
│  │  │  │ Frontend   │  │  │  │ Frontend   │  │      │  │
│  │  │  │ Pod        │  │  │  │ Pod        │  │      │  │
│  │  │  └────────────┘  │  │  └────────────┘  │      │  │
│  │  └──────────────────┘  └──────────────────┘      │  │
│  │         │                                  │       │  │
│  │         └──────────────────────────────────┘       │  │
│  │                     │                              │  │
│  │  ┌──────────────────┴──────────────────┐          │  │
│  │  │  Persistent Volumes (EBS)           │          │  │
│  │  │  • Database (10GB)                   │          │  │
│  │  │  • Images (50GB)                     │          │  │
│  │  │  • Logs (5GB)                        │          │  │
│  │  └──────────────────────────────────────┘          │  │
│  └─────────────────────────────────────────────────────┘  │
│                         │                                  │
│  ┌──────────────────────┴──────────────────────┐          │
│  │         AWS Load Balancer (ALB)             │          │
│  │    • Routes traffic to services            │          │
│  │    • SSL/TLS termination                   │          │
│  │    • Health checks                         │          │
│  └──────────────────────┬──────────────────────┘          │
│                         │                                  │
│  ┌──────────────────────┴──────────────────────┐          │
│  │       EC2 Container Registry (ECR)          │          │
│  │    • canvas3t-backend:latest               │          │
│  │    • canvas3t-frontend:latest              │          │
│  └───────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────┘

                      Internet
                          │
               ┌───────────┴───────────┐
               │                       │
         ┌─────▼──────┐         ┌──────▼─────┐
         │  Frontend   │         │   API      │
         │  (React)    │         │  (Flask)   │
         └─────────────┘         └────────────┘
```

---

## 🔐 Security Notes

### Immediate Actions
1. **Change Secrets** - Don't use default values
   ```powershell
   kubectl edit secret canvas3t-secrets -n canvas3t
   ```

2. **Enable HTTPS** - Configure SSL certificate
   ```yaml
   # Update in kubernetes/04-ingress-network.yaml
   alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:...
   ```

3. **Update Network Policies** - Restrict traffic as needed
   ```powershell
   kubectl get networkpolicy -n canvas3t
   ```

### Ongoing
- Monitor CloudWatch logs for suspicious activity
- Keep Kubernetes version up-to-date
- Regularly rotate secrets
- Enable audit logging
- Set up RBAC policies

---

## 📞 Common Issues & Quick Fixes

### "Unable to connect to the server"
```powershell
# Update kubeconfig
aws eks update-kubeconfig --name canvas3t-cluster --region us-east-1
```

### "ImagePullBackOff"
```powershell
# Verify ECR credentials
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com
```

### "Pending" pods
```powershell
# Check available resources
kubectl describe node <node-name>

# Check event logs
kubectl get events -n canvas3t
```

### "Health check failing"
```powershell
# Test endpoint directly
kubectl exec -it <pod-name> -n canvas3t -- curl http://localhost:5000/api/health
```

See **[KUBERNETES_COMMANDS_REFERENCE.md](KUBERNETES_COMMANDS_REFERENCE.md)** for more troubleshooting.

---

## 🎓 Learning Path

1. **Beginner**: Start with EKS_QUICK_START.md and deploy using the script
2. **Intermediate**: Read EKS_DEPLOYMENT_GUIDE.md and understand each component
3. **Advanced**: Study PRODUCTION_DEPLOYMENT.md and KUBERNETES_COMMANDS_REFERENCE.md
4. **Expert**: Customize manifests, set up monitoring, implement GitOps

---

## 🚀 Next Steps After Deployment

1. **Update DNS** - Point your domain to the ALB endpoint
2. **Enable HTTPS** - Configure SSL certificate
3. **Set up monitoring** - Enable CloudWatch Container Insights
4. **Configure backups** - Set up automated database backups
5. **Load testing** - Verify application performance
6. **User testing** - Test application functionality
7. **Production hardening** - Follow PRODUCTION_DEPLOYMENT.md checklist

---

## 📈 Scaling Strategy

### Horizontal Scaling (More Pods)
```powershell
# Already configured with HPA (Horizontal Pod Autoscaler)
# Automatically scales based on CPU/memory usage
# Min replicas: 2, Max replicas: 10 (backend), 6 (frontend)
```

### Vertical Scaling (Bigger Instances)
```powershell
# Change node type in EKS node group
aws eks update-nodegroup-config \
  --cluster-name canvas3t-cluster \
  --nodegroup-name canvas3t-nodes \
  --instance-types t3.large \
  --region us-east-1
```

### Storage Scaling
```powershell
# Expand PVC size
kubectl patch pvc canvas3t-images-pvc -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}' -n canvas3t
```

---

## 💾 Backup Strategy

- **Database**: Daily automated backups to S3
- **Images**: Weekly backups to S3
- **EBS Volumes**: Automated snapshots via AWS Data Lifecycle Manager
- **Retention**: 30 days minimum

---

## 🎯 Success Metrics

After deployment, verify:
- [ ] Application is accessible via ingress endpoint
- [ ] Frontend loads without errors
- [ ] Backend API responds to requests
- [ ] Database persistence working (create and retrieve paintings)
- [ ] Pods automatically restart on failure
- [ ] Scaling works under load
- [ ] Health checks passing
- [ ] Logs are collectible
- [ ] Backups are created

---

## 📚 Additional Resources

- **AWS EKS Best Practices**: https://aws.github.io/aws-eks-best-practices/
- **Kubernetes Security**: https://kubernetes.io/docs/concepts/security/
- **Container Security**: https://aws.amazon.com/containers/security/
- **Cost Optimization**: https://aws.amazon.com/architecture/cost-optimization/

---

## 🆘 Getting Help

1. Check **[KUBERNETES_COMMANDS_REFERENCE.md](KUBERNETES_COMMANDS_REFERENCE.md)** troubleshooting section
2. Review AWS CloudWatch logs
3. Check kubectl describe and logs output
4. Visit AWS Forums: https://forums.aws.amazon.com/forum.jspa?forumID=185
5. Read AWS EKS Documentation: https://docs.aws.amazon.com/eks/

---

## ✨ What's Included

✅ Complete EKS deployment guide
✅ Kubernetes manifests (ready to use)
✅ Automated deployment scripts (PowerShell & Bash)
✅ Infrastructure setup automation
✅ Production security checklist
✅ Monitoring and logging setup
✅ Backup and disaster recovery procedures
✅ Troubleshooting guide
✅ kubectl commands reference
✅ Cost optimization tips

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-18 | Initial release |

---

**Happy Deploying! 🚀**

For questions or issues, refer to the specific documentation file mentioned above.
