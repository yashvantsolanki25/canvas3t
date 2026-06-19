# 🎯 Post-Deployment Verification Checklist

Use this checklist to verify your Canvas3T EKS deployment is working correctly.

## ✅ Pre-Verification Prerequisites

Before starting, ensure you have:
- [ ] AWS CLI configured (`aws configure`)
- [ ] kubectl configured (`aws eks update-kubeconfig ...`)
- [ ] Your cluster is created and running
- [ ] Docker images are pushed to ECR

---

## 🔍 Kubernetes Cluster Verification

### Step 1: Verify Cluster Status
```powershell
# Check cluster is accessible
kubectl cluster-info

# Expected output: Shows cluster endpoint and DNS
```
- [ ] Cluster endpoint is accessible
- [ ] DNS component is running

### Step 2: Verify Nodes
```powershell
# Check all nodes are ready
kubectl get nodes -o wide

# Expected output: All nodes have STATUS "Ready"
```
- [ ] All nodes show STATUS: Ready
- [ ] Correct number of nodes (should match your configuration)
- [ ] All nodes have IP addresses assigned

### Step 3: Verify System Pods
```powershell
# Check kube-system namespace
kubectl get pods -n kube-system

# Expected output: Most pods running (some may be pending initially)
```
- [ ] Core DNS pods running
- [ ] kube-proxy pods running
- [ ] No pods in CrashLoopBackOff

---

## 📦 Namespace & Resources Verification

### Step 4: Verify Namespace
```powershell
# Check canvas3t namespace exists
kubectl get namespace canvas3t

# Expected output: Active namespace
```
- [ ] Namespace "canvas3t" exists
- [ ] Namespace status is "Active"

### Step 5: Verify ConfigMap
```powershell
# Check ConfigMap
kubectl get configmap -n canvas3t

# Check ConfigMap contents
kubectl get configmap canvas3t-config -n canvas3t -o yaml
```
- [ ] ConfigMap "canvas3t-config" exists
- [ ] Contains: FLASK_ENV, FLASK_APP, RESULTS_PER_PAGE

### Step 6: Verify Secrets
```powershell
# Check Secrets
kubectl get secrets -n canvas3t

# Check ECR secret exists
kubectl get secret ecr-secret -n canvas3t
```
- [ ] Secret "canvas3t-secrets" exists
- [ ] Secret "ecr-secret" exists

---

## 💾 Storage Verification

### Step 7: Verify Storage Class
```powershell
# Check Storage Classes
kubectl get storageclass

# Expected output: gp2 storage class available
```
- [ ] Storage class "gp2" exists
- [ ] Status shows it's available

### Step 8: Verify PersistentVolumeClaims
```powershell
# Check PVCs
kubectl get pvc -n canvas3t

# Expected output: All PVCs bound to PVs
```
- [ ] PVC "canvas3t-db-pvc" exists
- [ ] PVC "canvas3t-images-pvc" exists  
- [ ] PVC "canvas3t-logs-pvc" exists
- [ ] All PVCs have STATUS: "Bound"

### Step 9: Verify Persistent Volumes
```powershell
# Check PVs
kubectl get pv

# Should see corresponding PVs for the PVCs
```
- [ ] PVs are created for each PVC
- [ ] PV status shows "Bound"

---

## 🚀 Deployment Verification

### Step 10: Verify Backend Deployment
```powershell
# Check backend deployment
kubectl get deployment -n canvas3t

# Check pod status
kubectl get pods -l app=canvas3t-backend -n canvas3t

# Check deployment details
kubectl describe deployment canvas3t-backend -n canvas3t
```
- [ ] Deployment "canvas3t-backend" exists
- [ ] Deployment has 2 replicas (or configured number)
- [ ] All backend pods are "Running"
- [ ] All pods are "Ready"

### Step 11: Verify Frontend Deployment
```powershell
# Check frontend deployment
kubectl get deployment -n canvas3t

# Check pod status
kubectl get pods -l app=canvas3t-frontend -n canvas3t

# Check deployment details
kubectl describe deployment canvas3t-frontend -n canvas3t
```
- [ ] Deployment "canvas3t-frontend" exists
- [ ] Deployment has 2 replicas (or configured number)
- [ ] All frontend pods are "Running"
- [ ] All pods are "Ready"

### Step 12: Check Deployment Rollout Status
```powershell
# Check backend rollout
kubectl rollout status deployment/canvas3t-backend -n canvas3t

# Check frontend rollout
kubectl rollout status deployment/canvas3t-frontend -n canvas3t

# Expected output: "deployment "canvas3t-backend" successfully rolled out"
```
- [ ] Backend rollout successful
- [ ] Frontend rollout successful

---

## 🔌 Service Verification

### Step 13: Verify Services
```powershell
# Check all services
kubectl get svc -n canvas3t

# Check backend service
kubectl describe svc canvas3t-backend -n canvas3t

# Check frontend service
kubectl describe svc canvas3t-frontend -n canvas3t
```
- [ ] Service "canvas3t-backend" exists, type: ClusterIP
- [ ] Service "canvas3t-frontend" exists, type: ClusterIP
- [ ] Both services have Endpoints (active pods)

### Step 14: Verify Service Discovery
```powershell
# Test DNS from a pod
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- nslookup canvas3t-frontend

# Expected output: IP address of frontend service
```
- [ ] Services are discoverable by DNS
- [ ] Service IPs are assigned

---

## 🌐 Ingress Verification

### Step 15: Verify Ingress
```powershell
# Check ingress
kubectl get ingress -n canvas3t

# Check ingress details
kubectl describe ingress canvas3t-ingress -n canvas3t

# Get ingress endpoint
kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```
- [ ] Ingress "canvas3t-ingress" exists
- [ ] Ingress class is "alb" (AWS Load Balancer)
- [ ] ALB endpoint is assigned (not <pending>)
- [ ] Rules are configured for frontend and backend

### Step 16: Verify ALB
```powershell
# List load balancers
aws elbv2 describe-load-balancers --region us-east-1

# Get ALB URL (should match ingress endpoint)
$ALB_DNS = kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
Write-Host "ALB Endpoint: $ALB_DNS"
```
- [ ] ALB is created in AWS
- [ ] ALB has "active" state
- [ ] Listeners are configured (port 80, 443)

---

## 🏥 Health Check Verification

### Step 17: Verify Liveness Probes
```powershell
# Check if pods are passing liveness probes
kubectl get pods -n canvas3t -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# Get detailed pod info
kubectl describe pods -n canvas3t | grep -i "ready\|failed"
```
- [ ] All pods show "Ready" condition
- [ ] No pods show failed liveness probes

### Step 18: Verify Readiness Probes
```powershell
# Check backend API health
kubectl port-forward svc/canvas3t-backend 5000:5000 -n canvas3t

# In another terminal, test the health endpoint
curl http://localhost:5000/api/health

# Expected output: {"status": "ok"} or similar
```
- [ ] Backend API responds to health check
- [ ] Response includes status: "ok"

### Step 19: Verify Frontend Accessibility
```powershell
# Check frontend is serving
kubectl port-forward svc/canvas3t-frontend 4173:4173 -n canvas3t

# In another terminal, test frontend
curl http://localhost:4173

# Expected output: HTML content or index file
```
- [ ] Frontend responds to HTTP requests
- [ ] Frontend returns HTML content

---

## 📊 Auto-Scaling Verification

### Step 20: Verify HPA
```powershell
# Check Horizontal Pod Autoscaler
kubectl get hpa -n canvas3t

# Detailed HPA status
kubectl describe hpa canvas3t-backend-hpa -n canvas3t
```
- [ ] HPA "canvas3t-backend-hpa" exists
- [ ] HPA "canvas3t-frontend-hpa" exists
- [ ] Both showing current metrics

### Step 21: Verify Resource Metrics
```powershell
# Check pod resource usage (requires metrics-server)
kubectl top pods -n canvas3t

# Check node resource usage
kubectl top nodes

# Expected: Shows CPU and Memory usage
```
- [ ] Metrics-server is installed
- [ ] Pod metrics are available
- [ ] Node metrics are available

---

## 🔐 Security Verification

### Step 22: Verify Network Policies
```powershell
# Check network policies
kubectl get networkpolicy -n canvas3t

# Describe network policy
kubectl describe networkpolicy canvas3t-network-policy -n canvas3t
```
- [ ] Network policy exists
- [ ] Ingress rules are defined
- [ ] Egress rules are defined

### Step 23: Verify Pod Security
```powershell
# Check pod security context
kubectl get pods -n canvas3t -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext}{"\n"}{end}'

# Verify pods are not running as root
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- id
# Expected: uid != 0 (not root)
```
- [ ] Pods have security context configured
- [ ] Pods running as non-root user

---

## 📝 Logging Verification

### Step 24: Verify Logs Are Collectible
```powershell
# Check backend logs
kubectl logs deployment/canvas3t-backend -n canvas3t --tail=20

# Check frontend logs
kubectl logs deployment/canvas3t-frontend -n canvas3t --tail=20

# Check for errors
kubectl logs deployment/canvas3t-backend -n canvas3t | grep -i error
```
- [ ] Backend logs are available
- [ ] Frontend logs are available
- [ ] No critical errors in logs

### Step 25: Verify Log Streaming
```powershell
# Stream logs in real-time
kubectl logs -f deployment/canvas3t-backend -n canvas3t

# (Press Ctrl+C to stop)
```
- [ ] Can stream logs continuously
- [ ] No permission errors

---

## 🌍 External Access Verification

### Step 26: Verify External URL Access
```powershell
# Get ALB endpoint
$ALB_ENDPOINT = kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Test frontend
curl http://$ALB_ENDPOINT

# Test backend API
curl http://$ALB_ENDPOINT/api/health

# Test with browser
Start-Process "http://$ALB_ENDPOINT"
```
- [ ] Frontend is accessible via ALB endpoint
- [ ] API endpoint is accessible
- [ ] Browser can load the application

### Step 27: Verify Domain DNS (if configured)
```powershell
# Test domain resolution
nslookup yourdomain.com

# Test domain access
curl http://yourdomain.com

# Test API via domain
curl http://yourdomain.com/api/health
```
- [ ] Domain DNS resolves to ALB IP
- [ ] Application loads via domain
- [ ] API is accessible via domain

---

## 🔄 Application Functionality Verification

### Step 28: Test Basic API Endpoints
```powershell
# Get ALB endpoint
$API_URL = "http://$(kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')/api"

# Test health
curl "$API_URL/health"

# Test if database is working
curl "$API_URL/paintings"

# Test authentication endpoints (if applicable)
curl "$API_URL/auth/status"
```
- [ ] /api/health returns 200 OK
- [ ] /api/paintings returns data or empty list
- [ ] No 500 errors from backend

### Step 29: Test File Upload (if applicable)
```powershell
# Create test image
$testImage = @"
Test image content
"@

# Upload to backend (if upload endpoint exists)
# curl -F "file=@testimage.jpg" "$API_URL/upload"

# Check if files are stored
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- ls -la /app/images
```
- [ ] File upload works (if applicable)
- [ ] Files are persisted in PVC

### Step 30: Test Database Persistence
```powershell
# Check database file exists
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- ls -la /app/db/

# Check database size
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- du -sh /app/db/
```
- [ ] Database file exists
- [ ] Database file size > 0 (has data)

---

## 🚨 Events and Warnings

### Step 31: Check for Warnings or Errors
```powershell
# Get all events
kubectl get events -n canvas3t --sort-by='.lastTimestamp'

# Look for errors
kubectl get events -n canvas3t | grep -i "error\|warning\|failed"

# Check pod events specifically
kubectl describe pods -n canvas3t | grep -A 5 "Events:"
```
- [ ] No CrashLoopBackOff events
- [ ] No ImagePullBackOff events
- [ ] No OOMKilled events
- [ ] No Failed events

---

## 📈 Performance Verification

### Step 32: Check Resource Usage
```powershell
# Pod resource usage
kubectl top pods -n canvas3t --containers

# Node resource usage
kubectl top nodes

# Check if any pod is hitting limits
kubectl get pods -n canvas3t -o json | jq '.items[] | {name: .metadata.name, limits: .spec.containers[].resources.limits}'
```
- [ ] CPU usage reasonable (< 70%)
- [ ] Memory usage reasonable (< 80%)
- [ ] No pods hitting resource limits

### Step 33: Performance Test
```powershell
# Simple load test
for ($i = 0; $i -lt 100; $i++) {
    curl -s "http://$(kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')/api/health" > $null
    Write-Host "Request $i completed"
}

# Monitor pod CPU/memory during test
kubectl top pods -n canvas3t -w
```
- [ ] Application handles concurrent requests
- [ ] Response times are acceptable (< 1 second)
- [ ] No errors during load test

---

## 🎯 Final Validation

### Step 34: Complete Checklist Review
```powershell
# Generate summary report
Write-Host "=== Deployment Verification Summary ===" -ForegroundColor Green
Write-Host "Cluster: $(kubectl cluster-info | grep 'Kubernetes master' | awk '{print $NF}')" -ForegroundColor Yellow
Write-Host "Nodes: $(kubectl get nodes --no-headers | wc -l)" -ForegroundColor Yellow
Write-Host "Pods running: $(kubectl get pods -n canvas3t --no-headers | wc -l)" -ForegroundColor Yellow
Write-Host "ALB endpoint: $(kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')" -ForegroundColor Yellow
```

---

## ✨ Deployment Complete!

If you've checked all boxes above, your Canvas3T application is successfully deployed on EKS! 🎉

### Next Steps:
1. **Monitor** - Set up CloudWatch alerts and dashboards
2. **Backup** - Configure automated database backups
3. **Scale** - Adjust HPA settings based on load
4. **Security** - Review and implement security best practices
5. **Optimize** - Monitor costs and right-size instances

### Useful Commands for Ongoing Management:

```powershell
# View real-time logs
kubectl logs -f deployment/canvas3t-backend -n canvas3t

# Scale deployment
kubectl scale deployment canvas3t-backend --replicas=3 -n canvas3t

# Update application
kubectl set image deployment/canvas3t-backend backend=YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/canvas3t-backend:v1.1.0 -n canvas3t

# View resource usage
kubectl top pods -n canvas3t

# Get pod details
kubectl describe pod <pod-name> -n canvas3t

# Access application locally
kubectl port-forward svc/canvas3t-backend 5000:5000 -n canvas3t
```

---

**Congratulations! Your Canvas3T application is now live on AWS EKS! 🚀**

For any issues, refer to:
- [KUBERNETES_COMMANDS_REFERENCE.md](KUBERNETES_COMMANDS_REFERENCE.md) - Troubleshooting section
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - Production issues
- AWS Documentation: https://docs.aws.amazon.com/eks/
