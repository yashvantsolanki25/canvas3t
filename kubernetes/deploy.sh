#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
REGION="us-east-1"
CLUSTER_NAME="canvas3t-cluster"
NAMESPACE="canvas3t"

echo -e "${BLUE}=== Canvas3T EKS Deployment Script ===${NC}\n"

# Function to print step
print_step() {
    echo -e "${GREEN}[STEP] $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Step 1: Configure AWS CLI
print_step "Configuring AWS credentials..."
aws sts get-caller-identity > /dev/null 2>&1
if [ $? -ne 0 ]; then
    print_error "AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi
echo "✓ AWS credentials configured"

# Step 2: Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
print_step "AWS Account ID: $AWS_ACCOUNT_ID"

# Step 3: Create ECR repositories
print_step "Creating ECR repositories..."
aws ecr create-repository \
  --repository-name canvas3t-backend \
  --region $REGION \
  --image-scanning-configuration scanOnPush=true \
  2>/dev/null || echo "Repository canvas3t-backend already exists"

aws ecr create-repository \
  --repository-name canvas3t-frontend \
  --region $REGION \
  --image-scanning-configuration scanOnPush=true \
  2>/dev/null || echo "Repository canvas3t-frontend already exists"

echo "✓ ECR repositories ready"

# Step 4: Build images
print_step "Building Docker images..."
docker build -f Dockerfile -t canvas3t-backend:latest . || exit 1
docker build -f frontend/Dockerfile -t canvas3t-frontend:latest . || exit 1
echo "✓ Docker images built"

# Step 5: Login to ECR
print_step "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
echo "✓ Logged into ECR"

# Step 6: Tag and push images
print_step "Tagging and pushing images to ECR..."
docker tag canvas3t-backend:latest "$ECR_REGISTRY/canvas3t-backend:latest"
docker tag canvas3t-backend:latest "$ECR_REGISTRY/canvas3t-backend:v1.0.0"
docker push "$ECR_REGISTRY/canvas3t-backend:latest"
docker push "$ECR_REGISTRY/canvas3t-backend:v1.0.0"

docker tag canvas3t-frontend:latest "$ECR_REGISTRY/canvas3t-frontend:latest"
docker tag canvas3t-frontend:latest "$ECR_REGISTRY/canvas3t-frontend:v1.0.0"
docker push "$ECR_REGISTRY/canvas3t-frontend:latest"
docker push "$ECR_REGISTRY/canvas3t-frontend:v1.0.0"
echo "✓ Images pushed to ECR"

# Step 7: Update kubeconfig
print_step "Updating kubeconfig..."
aws eks update-kubeconfig --name $CLUSTER_NAME --region $REGION
echo "✓ Kubeconfig updated"

# Step 8: Create ECR secret for image pull
print_step "Creating ECR authentication secret..."
ECR_PASSWORD=$(aws ecr get-login-password --region $REGION)
kubectl create secret docker-registry ecr-secret \
  --docker-server="$ECR_REGISTRY" \
  --docker-username=AWS \
  --docker-password="$ECR_PASSWORD" \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -
echo "✓ ECR secret created"

# Step 9: Update YAML files with actual AWS Account ID
print_step "Updating Kubernetes manifests with AWS Account ID..."
for file in kubernetes/*.yaml; do
    if [ -f "$file" ]; then
        sed -i "s|YOUR_AWS_ACCOUNT_ID|$AWS_ACCOUNT_ID|g" "$file"
        sed -i "s|yourdomain.com|your-actual-domain.com|g" "$file"
    fi
done
echo "✓ Manifests updated"

# Step 10: Apply Kubernetes manifests
print_step "Deploying to Kubernetes..."
kubectl apply -f kubernetes/00-namespace-config.yaml
sleep 2
kubectl apply -f kubernetes/01-storage.yaml
sleep 2
kubectl apply -f kubernetes/02-backend-deployment.yaml
sleep 2
kubectl apply -f kubernetes/03-frontend-deployment.yaml
sleep 2
kubectl apply -f kubernetes/04-ingress-network.yaml
sleep 2
kubectl apply -f kubernetes/05-hpa.yaml
echo "✓ Deployments applied"

# Step 11: Wait for deployments to be ready
print_step "Waiting for deployments to be ready..."
kubectl rollout status deployment/canvas3t-backend -n $NAMESPACE
kubectl rollout status deployment/canvas3t-frontend -n $NAMESPACE
echo "✓ Deployments are ready"

# Step 12: Display deployment information
print_step "Deployment Information:"
echo ""
echo "Namespace: $NAMESPACE"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo ""

echo "Deployments:"
kubectl get deployments -n $NAMESPACE

echo ""
echo "Services:"
kubectl get services -n $NAMESPACE

echo ""
echo "Ingress:"
kubectl get ingress -n $NAMESPACE

echo ""
echo "Pods:"
kubectl get pods -n $NAMESPACE

echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Update your DNS records to point to the ALB endpoint (see ingress EXTERNAL-IP)"
echo "2. Update the SECRET_KEY in secrets for production"
echo "3. Update VITE_API_URL in frontend deployment"
echo "4. Update yourdomain.com in ingress configuration"
echo ""
echo "Useful commands:"
echo "  View logs: kubectl logs -f deployment/canvas3t-backend -n $NAMESPACE"
echo "  Port forward: kubectl port-forward svc/canvas3t-backend 5000:5000 -n $NAMESPACE"
echo "  Scale backend: kubectl scale deployment canvas3t-backend --replicas=3 -n $NAMESPACE"
