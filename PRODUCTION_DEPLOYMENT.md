# Canvas3T EKS - Production Deployment Guide

## 🚀 Pre-Deployment Checklist

### Security
- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Use AWS Secrets Manager for sensitive data
- [ ] Enable encryption at rest for EBS volumes
- [ ] Enable VPC Flow Logs for network monitoring
- [ ] Set up IAM policies with least privilege
- [ ] Use security groups to restrict traffic
- [ ] Enable ALB SSL/TLS with ACM certificate
- [ ] Enable Pod Security Standards

### Networking
- [ ] Reserve static IP for NAT Gateway
- [ ] Configure private subnets for nodes
- [ ] Set up VPC endpoints for AWS services
- [ ] Configure network policies
- [ ] Set up AWS WAF for ALB (optional)

### Database & Storage
- [ ] Enable EBS encryption for data volumes
- [ ] Set up automated backups
- [ ] Test restore procedures
- [ ] Configure volume snapshots
- [ ] Monitor storage usage

### Monitoring & Logging
- [ ] Deploy Prometheus for metrics
- [ ] Deploy Grafana for dashboards
- [ ] Enable CloudWatch Container Insights
- [ ] Set up log aggregation (CloudWatch Logs/ELK)
- [ ] Configure alarms for critical metrics
- [ ] Set up email/Slack notifications

### High Availability
- [ ] Configure multiple availability zones
- [ ] Set up Pod Disruption Budgets
- [ ] Enable cluster autoscaling
- [ ] Configure horizontal pod autoscaling
- [ ] Set up multi-region backup

---

## 🔐 Production Security Configuration

### 1. Update Secrets

```powershell
# Generate secure random SECRET_KEY
$secretKey = -join ((0..31) | ForEach-Object { [char][byte](Get-Random -Minimum 33 -Maximum 127) })

# Delete old secret
kubectl delete secret canvas3t-secrets -n canvas3t

# Create new secret with strong values
kubectl create secret generic canvas3t-secrets `
  --from-literal=SECRET_KEY="$secretKey" `
  --from-literal=DB_PASSWORD="$(openssl rand -base64 32)" `
  --from-literal=JWT_SECRET="$(openssl rand -base64 32)" `
  -n canvas3t
```

### 2. Enable SSL/TLS with AWS Certificate Manager

```powershell
# Create or import certificate in ACM
$CERT_ARN = "arn:aws:acm:us-east-1:ACCOUNT_ID:certificate/CERT_ID"

# Update ingress annotations
kubectl patch ingress canvas3t-ingress -n canvas3t --type merge -p '{
  "metadata": {
    "annotations": {
      "alb.ingress.kubernetes.io/listen-ports": "[{\"HTTP\": 80}, {\"HTTPS\": 443}]",
      "alb.ingress.kubernetes.io/ssl-redirect": "443",
      "alb.ingress.kubernetes.io/certificate-arn": "'$CERT_ARN'"
    }
  }
}'
```

### 3. Network Policies

```yaml
# Already applied in 04-ingress-network.yaml
# Restricts ingress/egress traffic to only required ports

# Verify network policies
kubectl get networkpolicy -n canvas3t
```

### 4. Pod Security Standards

```powershell
# Apply pod security standards
kubectl label namespace canvas3t pod-security.kubernetes.io/enforce=restricted pod-security.kubernetes.io/audit=restricted pod-security.kubernetes.io/warn=restricted
```

---

## 📊 Monitoring Setup

### 1. Install Prometheus

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f - <<EOF
prometheus:
  prometheusSpec:
    retention: 30d
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "512Mi"
        cpu: "500m"
grafana:
  adminPassword: "your-secure-password"
EOF
```

### 2. Configure CloudWatch Container Insights

```powershell
# Create namespace for monitoring
kubectl create namespace amazon-cloudwatch

# Create IAM role for Container Insights
$role_doc = @"
{
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
}
"@

aws iam create-role --role-name CloudWatchContainerInsightsRole --assume-role-policy-document $role_doc

aws iam attach-role-policy `
  --role-name CloudWatchContainerInsightsRole `
  --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentAdminPolicy

# Apply CloudWatch agent to cluster
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-eks-deploy-cloudwatch-container-insights/main/deployment-yaml/aws-cloudwatch-metrics-elbv2-deployment.yaml
```

### 3. Set Up CloudWatch Alarms

```powershell
# CPU usage alarm
aws cloudwatch put-metric-alarm `
  --alarm-name canvas3t-high-cpu `
  --alarm-description "Alert when CPU usage is high" `
  --metric-name CPUUtilization `
  --namespace AWS/ECS `
  --statistic Average `
  --period 300 `
  --threshold 80 `
  --comparison-operator GreaterThanThreshold

# Memory usage alarm
aws cloudwatch put-metric-alarm `
  --alarm-name canvas3t-high-memory `
  --alarm-description "Alert when memory usage is high" `
  --metric-name MemoryUtilization `
  --namespace AWS/ECS `
  --statistic Average `
  --period 300 `
  --threshold 85 `
  --comparison-operator GreaterThanThreshold
```

---

## 🔄 Backup & Disaster Recovery

### 1. Database Backup Schedule

```powershell
# Create CronJob for daily backups
kubectl apply -f - -n canvas3t <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/canvas3t-backend:latest
            command:
            - /bin/sh
            - -c
            - |
              tar -czf /tmp/db-backup-\$(date +%Y%m%d).tar.gz /app/db
              aws s3 cp /tmp/db-backup-\$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
          restartPolicy: OnFailure
EOF
```

### 2. Image Backup

```powershell
# Backup images to S3
$timestamp = Get-Date -Format "yyyyMMdd"
kubectl exec -it canvas3t-backend-xxxxx -n canvas3t -- \
  tar -czf /tmp/images-backup-$timestamp.tar.gz /app/images
kubectl cp canvas3t/canvas3t-backend-xxxxx:/tmp/images-backup-$timestamp.tar.gz ./
aws s3 cp images-backup-$timestamp.tar.gz s3://your-backup-bucket/
```

### 3. EBS Snapshot Schedule

```powershell
# Create Data Lifecycle Manager policy for automatic snapshots
aws dlm create-lifecycle-policy `
  --policy-type EBS_SNAPSHOT_MANAGEMENT `
  --description "Daily snapshots of canvas3t volumes" `
  --execution-role-arn arn:aws:iam::ACCOUNT_ID:role/service-role/AWSDataLifecycleManagerDefaultRole `
  --state ENABLED `
  --policy-details '{
    "PolicyType": "EBS_SNAPSHOT_MANAGEMENT",
    "ResourceTypes": ["VOLUME"],
    "TargetTags": [{"Key":"Application","Values":["canvas3t"]}],
    "Schedules": [{
      "Name": "Daily snapshots",
      "CreateRule": {"Interval":24,"IntervalUnit":"HOURS","Times":["02:00"]},
      "RetainRule": {"Count":7},
      "TagsToAdd": [{"Key":"Type","Value":"Backup"}],
      "CopyTags": true
    }]
  }'
```

---

## 🚨 Troubleshooting Guide

### Issue: Pods Not Starting

**Symptoms**: Pods stuck in `Pending` or `CrashLoopBackOff`

**Diagnosis**:
```powershell
# Check pod status
kubectl describe pod <pod-name> -n canvas3t

# Check events
kubectl get events -n canvas3t --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n canvas3t --previous
```

**Solutions**:
- **Insufficient resources**: Scale down other workloads or increase node count
- **Image pull errors**: Verify ECR login and secret configuration
- **Health check failures**: Check endpoint availability

### Issue: Database Connection Errors

**Symptoms**: Backend pods fail health checks

**Diagnosis**:
```powershell
# Test from pod
kubectl exec -it <pod-name> -n canvas3t -- curl http://localhost:5000/api/health

# Check database volume
kubectl exec -it <pod-name> -n canvas3t -- ls -la /app/db/

# Check PVC status
kubectl describe pvc canvas3t-db-pvc -n canvas3t
```

**Solutions**:
- Ensure PVC is mounted correctly
- Check PVC storage availability
- Verify file permissions inside pod

### Issue: High Memory Usage

**Symptoms**: Pods getting OOMKilled, memory pressure on nodes

**Diagnosis**:
```powershell
# Check memory usage
kubectl top pods -n canvas3t
kubectl top nodes

# Check memory requests/limits
kubectl describe pod <pod-name> -n canvas3t | grep -A 5 "Limits"

# Check memory pressure events
kubectl get events -n canvas3t | grep -i memory
```

**Solutions**:
- Increase memory limits in deployment
- Check for memory leaks in application code
- Scale to more nodes
- Reduce HPA max replicas if overscaling

### Issue: Ingress Not Getting IP

**Symptoms**: Ingress shows `<pending>` for EXTERNAL-IP

**Diagnosis**:
```powershell
# Check ingress status
kubectl describe ingress canvas3t-ingress -n canvas3t

# Check ALB controller logs
kubectl logs -l app.kubernetes.io/name=aws-load-balancer-controller -n kube-system

# Check subnets are tagged correctly
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxxxx"
```

**Solutions**:
- Verify ALB controller is installed
- Ensure subnets are tagged with `kubernetes.io/role/elb=1`
- Check security group allows ALB traffic
- Wait 2-3 minutes for ALB provisioning

### Issue: Certificate Errors

**Symptoms**: HTTPS connection fails, certificate not valid

**Diagnosis**:
```powershell
# Check ACM certificate
aws acm describe-certificate --certificate-arn arn:aws:acm:us-east-1:ACCOUNT:certificate/ID

# Check ingress annotations
kubectl get ingress canvas3t-ingress -n canvas3t -o yaml | grep -i cert

# Test SSL
curl -v https://your-domain.com
```

**Solutions**:
- Verify certificate ARN in ingress annotations
- Ensure certificate is valid and not expired
- Check DNS CNAME records point to ALB
- Wait for ALB listener update (5-10 minutes)

---

## 📈 Performance Tuning

### 1. Optimize Resource Requests/Limits

```powershell
# Monitor current usage
kubectl top pods -n canvas3t --containers

# Update deployment with optimized values
kubectl set resources deployment canvas3t-backend \
  --requests=cpu=200m,memory=256Mi \
  --limits=cpu=500m,memory=512Mi \
  -n canvas3t
```

### 2. Configure HPA Appropriately

```powershell
# View current HPA
kubectl get hpa -n canvas3t

# Update HPA thresholds
kubectl patch hpa canvas3t-backend-hpa -n canvas3t --type merge -p '{
  "spec": {
    "maxReplicas": 10,
    "metrics": [
      {
        "type": "Resource",
        "resource": {
          "name": "cpu",
          "target": {
            "type": "Utilization",
            "averageUtilization": 65
          }
        }
      }
    ]
  }
}'
```

### 3. Database Query Optimization

```powershell
# Connect to database from pod
kubectl exec -it <pod-name> -n canvas3t -- sqlite3 /app/db/app.db

# Inside sqlite3:
# .tables
# SELECT COUNT(*) FROM table_name;
# EXPLAIN QUERY PLAN SELECT * FROM paintings;
```

### 4. Cache Configuration

```powershell
# Update Flask configuration for caching
kubectl set env deployment/canvas3t-backend \
  CACHE_TYPE=simple \
  CACHE_TIMEOUT=300 \
  -n canvas3t
```

---

## 🔍 Logging Best Practices

### 1. Configure Log Retention

```powershell
# Update deployment to set log retention
kubectl patch deployment canvas3t-backend -n canvas3t --type merge -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "backend",
          "env": [
            {
              "name": "LOG_LEVEL",
              "value": "INFO"
            }
          ]
        }]
      }
    }
  }
}'
```

### 2. Centralized Logging

```bash
# Install ELK Stack or Loki for log aggregation
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  -n logging --create-namespace \
  --set loki.persistence.enabled=true
```

### 3. Application Logging

Ensure your Flask app logs to stdout:
```python
import logging
logging.basicConfig(level=logging.INFO)
app.logger.info("Application started")
```

---

## ✅ Post-Deployment Validation

```powershell
# 1. Verify all pods are running
kubectl get pods -n canvas3t

# 2. Check deployments status
kubectl get deployment -n canvas3t -o wide

# 3. Verify services
kubectl get svc -n canvas3t

# 4. Check ingress is configured
kubectl get ingress -n canvas3t

# 5. Test connectivity
curl https://your-domain.com

# 6. Check metrics available
kubectl top pods -n canvas3t
kubectl top nodes

# 7. Verify persistent volumes
kubectl get pvc -n canvas3t

# 8. Check recent events
kubectl get events -n canvas3t --sort-by='.lastTimestamp' | tail -20

# 9. Test health endpoints
kubectl port-forward svc/canvas3t-backend 5000:5000 -n canvas3t
# In another terminal: curl http://localhost:5000/api/health

# 10. Load test (optional)
kubectl run -it --rm load-test --image=busybox -n canvas3t -- /bin/sh
# ab -n 1000 -c 100 https://your-domain.com/
```

---

## 🎯 Maintenance Schedule

**Daily**:
- Monitor pod health and logs
- Check resource usage
- Review CloudWatch alarms

**Weekly**:
- Review security group rules
- Check certificate expiration
- Analyze performance metrics

**Monthly**:
- Update Kubernetes version (if available)
- Rotate secrets
- Test disaster recovery procedures
- Review cost analysis

**Quarterly**:
- Security audit
- Backup restoration test
- Capacity planning review
- Update dependencies

---

## 📞 Support & Resources

- AWS EKS Documentation: https://docs.aws.amazon.com/eks/
- Kubernetes Official Docs: https://kubernetes.io/docs/
- Troubleshooting Guide: https://docs.aws.amazon.com/eks/latest/userguide/troubleshooting.html
- Community Forums: https://forums.aws.amazon.com/forum.jspa?forumID=185
- AWS Support: https://console.aws.amazon.com/support/

---

**Last Updated**: 2026-06-18
**Version**: 1.0
