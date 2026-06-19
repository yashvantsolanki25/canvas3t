# Kubernetes Helper Commands Script

## 🔍 Deployment Status

```powershell
# Check cluster status
kubectl cluster-info

# Check nodes
kubectl get nodes -o wide
kubectl describe node <node-name>

# Check all resources in namespace
kubectl get all -n canvas3t

# Check specific deployments
kubectl get deployment canvas3t-backend -n canvas3t -o yaml
kubectl describe deployment canvas3t-backend -n canvas3t
```

## 📊 Monitoring & Logging

```powershell
# Real-time logs
kubectl logs -f deployment/canvas3t-backend -n canvas3t
kubectl logs -f deployment/canvas3t-frontend -n canvas3t

# Logs from specific pod
kubectl logs canvas3t-backend-xxxxx -n canvas3t
kubectl logs canvas3t-backend-xxxxx -n canvas3t --previous  # Previous container logs

# Last N lines
kubectl logs -n canvas3t deployment/canvas3t-backend --tail=50

# Logs from specific time
kubectl logs -n canvas3t deployment/canvas3t-backend --since=1h

# Pod resource usage (requires metrics-server)
kubectl top pods -n canvas3t
kubectl top nodes

# Watch pod status
kubectl get pods -n canvas3t -w

# Events
kubectl get events -n canvas3t --sort-by='.lastTimestamp'
```

## 🔧 Scaling & Updates

```powershell
# Scale deployments
kubectl scale deployment canvas3t-backend --replicas=3 -n canvas3t
kubectl scale deployment canvas3t-frontend --replicas=2 -n canvas3t

# Set resource limits
kubectl set resources deployment canvas3t-backend --limits cpu=600m,memory=512Mi -n canvas3t

# Update image
kubectl set image deployment/canvas3t-backend backend=YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/canvas3t-backend:v1.1.0 -n canvas3t

# Watch rollout
kubectl rollout status deployment/canvas3t-backend -n canvas3t

# Rollback
kubectl rollout undo deployment/canvas3t-backend -n canvas3t
kubectl rollout undo deployment/canvas3t-backend --to-revision=1 -n canvas3t

# View rollout history
kubectl rollout history deployment/canvas3t-backend -n canvas3t
```

## 🚀 Port Forwarding

```powershell
# Forward local port to service
kubectl port-forward svc/canvas3t-backend 5000:5000 -n canvas3t
# Then: http://localhost:5000

kubectl port-forward svc/canvas3t-frontend 4173:4173 -n canvas3t
# Then: http://localhost:4173

# Forward to specific pod
kubectl port-forward canvas3t-backend-xxxxx 5000:5000 -n canvas3t
```

## 🔐 Secrets & Configuration

```powershell
# List secrets
kubectl get secrets -n canvas3t

# View secret values (base64 decoded)
$secret = kubectl get secret canvas3t-secrets -n canvas3t -o json | ConvertFrom-Json
$secret.data.SECRET_KEY | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }

# Update secret
kubectl delete secret canvas3t-secrets -n canvas3t
kubectl create secret generic canvas3t-secrets `
  --from-literal=SECRET_KEY="new-secret" `
  -n canvas3t

# Update ConfigMap
kubectl edit configmap canvas3t-config -n canvas3t

# View current config
kubectl get configmap canvas3t-config -n canvas3t -o yaml
```

## 📁 Storage Management

```powershell
# Check PVCs
kubectl get pvc -n canvas3t

# Check PV
kubectl get pv

# Describe PVC
kubectl describe pvc canvas3t-db-pvc -n canvas3t

# Check storage usage
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- df -h /app/db

# Backup database
mkdir -p ./backups
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- tar -czf /tmp/db-backup.tar.gz /app/db
kubectl cp canvas3t/canvas3t-backend-xxxxx:/tmp/db-backup.tar.gz ./backups/db-backup.tar.gz

# Restore database
kubectl cp ./backups/db-backup.tar.gz canvas3t/canvas3t-backend-xxxxx:/tmp/
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- tar -xzf /tmp/db-backup.tar.gz -C /
```

## 🌐 Networking

```powershell
# Check services
kubectl get svc -n canvas3t

# Check ingress
kubectl get ingress -n canvas3t -o wide

# Get Ingress details
kubectl describe ingress canvas3t-ingress -n canvas3t

# Get ALB endpoint
$ALB_ENDPOINT = kubectl get ingress canvas3t-ingress -n canvas3t -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
Write-Host $ALB_ENDPOINT

# Test connectivity
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- curl http://canvas3t-frontend:4173
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- curl http://localhost:5000/api/health

# Check network policies
kubectl get networkpolicy -n canvas3t
```

## 🩺 Troubleshooting

```powershell
# Describe pod for events and errors
kubectl describe pod <pod-name> -n canvas3t

# Get pod details
kubectl get pod <pod-name> -n canvas3t -o yaml

# Check pod startup logs
kubectl logs <pod-name> -n canvas3t --all-containers=true

# Debug with temporary pod
kubectl run -it --rm debug --image=busybox --restart=Never -n canvas3t -- /bin/sh

# Execute commands in running pod
kubectl exec -it <pod-name> -n canvas3t -- /bin/bash
# Inside pod:
# curl http://localhost:5000/api/health
# ps aux
# df -h

# Check DNS
kubectl exec -it <pod-name> -n canvas3t -- nslookup canvas3t-backend
kubectl exec -it <pod-name> -n canvas3t -- cat /etc/resolv.conf

# Check liveness/readiness probes
kubectl get pod <pod-name> -n canvas3t -o yaml | grep -A 15 "livenessProbe"
```

## 🔄 CRUD Operations

```powershell
# Create resources
kubectl apply -f kubernetes/manifests.yaml -n canvas3t

# Read resources
kubectl get deployment -n canvas3t
kubectl describe deployment canvas3t-backend -n canvas3t

# Update resources
kubectl apply -f kubernetes/manifests.yaml -n canvas3t  # If file changed
kubectl patch deployment canvas3t-backend -p '{"spec":{"replicas":3}}' -n canvas3t

# Delete resources
kubectl delete deployment canvas3t-backend -n canvas3t
kubectl delete -f kubernetes/manifests.yaml -n canvas3t

# Delete entire namespace
kubectl delete namespace canvas3t
```

## 📈 Performance

```powershell
# Install metrics-server (one-time)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Wait for metrics to be available
Start-Sleep -Seconds 30

# View resource usage
kubectl top nodes
kubectl top pods -n canvas3t
kubectl top pods -n canvas3t --containers

# Create load test
kubectl run -it --rm load-generator --image=busybox --restart=Never -n canvas3t -- /bin/sh -c "while sleep 0.01; do wget -q -O- http://canvas3t-backend/api/health; done"
```

## 🎯 Useful One-Liners

```powershell
# Get all pod IPs
kubectl get pods -n canvas3t -o wide

# Get pod by label
kubectl get pods -l app=canvas3t-backend -n canvas3t

# Delete all pods to force restart
kubectl delete pods --all -n canvas3t

# Get resource definitions
kubectl api-resources

# Get all API versions
kubectl api-versions

# Explain resource fields
kubectl explain pod
kubectl explain deployment.spec.template.spec

# Watch a resource
kubectl get pods -n canvas3t -w

# Get logs from all pods
kubectl logs -l app=canvas3t-backend -n canvas3t -f

# Export resources
kubectl get deployment canvas3t-backend -n canvas3t -o yaml > backup.yaml
```

## 📋 Debugging Checklists

### Pod Not Starting
1. `kubectl describe pod <name> -n canvas3t`
2. `kubectl logs <name> -n canvas3t`
3. `kubectl get events -n canvas3t`
4. Check image: `kubectl get pod <name> -n canvas3t -o jsonpath='{.spec.containers[0].image}'`
5. Check pull secrets: `kubectl get secrets -n canvas3t`

### Health Check Failing
1. `kubectl exec <name> -n canvas3t -- curl http://localhost:5000/api/health`
2. Check liveness probe: `kubectl get pod <name> -n canvas3t -o yaml | grep livenessProbe -A 10`
3. Check service: `kubectl get svc -n canvas3t`
4. Port forward and test locally

### Resource Issues
1. `kubectl top pods -n canvas3t`
2. Check resource requests/limits: `kubectl describe pod <name> -n canvas3t`
3. Check node capacity: `kubectl describe node <node-name>`
4. Check PVC: `kubectl get pvc -n canvas3t`

### Network Issues
1. Test pod connectivity: `kubectl exec <name> -n canvas3t -- curl http://service-name:port`
2. Check DNS: `kubectl exec <name> -n canvas3t -- nslookup service-name`
3. Check network policies: `kubectl get networkpolicy -n canvas3t`
4. Check ingress: `kubectl describe ingress -n canvas3t`

## 🚨 Emergency Commands

```powershell
# Force delete stuck pod
kubectl delete pod <name> -n canvas3t --grace-period=0 --force

# Restart deployment
kubectl rollout restart deployment/canvas3t-backend -n canvas3t

# Clear all failed pods
kubectl delete pods --field-selector status.phase=Failed -n canvas3t

# Emergency scale down
kubectl scale deployment canvas3t-backend --replicas=0 -n canvas3t

# Emergency scale up
kubectl scale deployment canvas3t-backend --replicas=1 -n canvas3t

# Drain node for maintenance
kubectl drain <node-name> --ignore-daemonsets

# Uncordon node after maintenance
kubectl uncordon <node-name>
```

---

**Pro Tip**: Create PowerShell aliases for frequently used commands:
```powershell
Set-Alias -Name kgp -Value "kubectl get pods -n canvas3t"
Set-Alias -Name kgl -Value "kubectl logs -f deployment/canvas3t-backend -n canvas3t"
Set-Alias -Name kgd -Value "kubectl get deployment -n canvas3t"
```

Add these to your PowerShell profile for persistence!
