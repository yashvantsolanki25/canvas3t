# Canvas3T EKS Deployment Script for Windows PowerShell

# Configuration
$REGION = "us-east-1"
$CLUSTER_NAME = "canvas3t-cluster"
$NAMESPACE = "canvas3t"
$PROJECT_ROOT = (Get-Location).Path

# Colors
$Green = 'Green'
$Red = 'Red'
$Blue = 'Cyan'

function Print-Step {
    param([string]$Message)
    Write-Host "[STEP] $Message" -ForegroundColor $Blue
}

function Print-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor $Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor $Red
}

Clear-Host
Write-Host "=== Canvas3T EKS Deployment Script ===" -ForegroundColor $Blue
Write-Host ""

# Step 1: Verify AWS credentials
Print-Step "Verifying AWS credentials..."
try {
    $AWSIdentity = aws sts get-caller-identity | ConvertFrom-Json
    $AWS_ACCOUNT_ID = $AWSIdentity.Account
    Print-Success "AWS credentials verified"
    Write-Host "Account ID: $AWS_ACCOUNT_ID"
}
catch {
    Print-Error "AWS credentials not configured. Run 'aws configure' first."
    exit 1
}

$ECR_REGISTRY = "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Step 2: Create ECR repositories
Print-Step "Creating ECR repositories..."
try {
    aws ecr create-repository `
        --repository-name canvas3t-backend `
        --region $REGION `
        --image-scanning-configuration scanOnPush=true `
        --output none 2>$null
    
    aws ecr create-repository `
        --repository-name canvas3t-frontend `
        --region $REGION `
        --image-scanning-configuration scanOnPush=true `
        --output none 2>$null
    
    Print-Success "ECR repositories ready"
}
catch {
    Write-Host "Note: Repositories may already exist" -ForegroundColor Yellow
}

# Step 3: Build Docker images
Print-Step "Building Docker images..."
try {
    docker build -f Dockerfile -t canvas3t-backend:latest .
    if ($LASTEXITCODE -ne 0) { throw "Backend build failed" }
    
    docker build -f frontend/Dockerfile -t canvas3t-frontend:latest .
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }
    
    Print-Success "Docker images built"
}
catch {
    Print-Error "Build failed: $_"
    exit 1
}

# Step 4: Login to ECR
Print-Step "Logging into ECR..."
try {
    $ECR_PASSWORD = aws ecr get-login-password --region $REGION
    $ECR_PASSWORD | docker login --username AWS --password-stdin $ECR_REGISTRY
    Print-Success "Logged into ECR"
}
catch {
    Print-Error "ECR login failed: $_"
    exit 1
}

# Step 5: Tag and push images
Print-Step "Tagging and pushing images to ECR..."
try {
    # Backend
    docker tag canvas3t-backend:latest "$ECR_REGISTRY/canvas3t-backend:latest"
    docker tag canvas3t-backend:latest "$ECR_REGISTRY/canvas3t-backend:v1.0.0"
    docker push "$ECR_REGISTRY/canvas3t-backend:latest"
    docker push "$ECR_REGISTRY/canvas3t-backend:v1.0.0"
    
    # Frontend
    docker tag canvas3t-frontend:latest "$ECR_REGISTRY/canvas3t-frontend:latest"
    docker tag canvas3t-frontend:latest "$ECR_REGISTRY/canvas3t-frontend:v1.0.0"
    docker push "$ECR_REGISTRY/canvas3t-frontend:latest"
    docker push "$ECR_REGISTRY/canvas3t-frontend:v1.0.0"
    
    Print-Success "Images pushed to ECR"
}
catch {
    Print-Error "Image push failed: $_"
    exit 1
}

# Step 6: Update kubeconfig
Print-Step "Updating kubeconfig..."
try {
    aws eks update-kubeconfig --name $CLUSTER_NAME --region $REGION
    Print-Success "Kubeconfig updated"
}
catch {
    Print-Error "Kubeconfig update failed: $_"
    exit 1
}

# Step 7: Create ECR secret
Print-Step "Creating ECR authentication secret..."
try {
    $ECR_PASSWORD = aws ecr get-login-password --region $REGION
    
    kubectl create secret docker-registry ecr-secret `
        --docker-server="$ECR_REGISTRY" `
        --docker-username=AWS `
        --docker-password=$ECR_PASSWORD `
        -n $NAMESPACE `
        --dry-run=client -o yaml | kubectl apply -f -
    
    Print-Success "ECR secret created"
}
catch {
    Print-Error "Secret creation failed: $_"
    exit 1
}

# Step 8: Update YAML files
Print-Step "Updating Kubernetes manifests..."
try {
    $KubernetesDir = Join-Path $PROJECT_ROOT "kubernetes"
    
    Get-ChildItem "$KubernetesDir\*.yaml" | ForEach-Object {
        $content = Get-Content $_.FullName -Raw
        $content = $content -replace "YOUR_AWS_ACCOUNT_ID", $AWS_ACCOUNT_ID
        $content = $content -replace "yourdomain\.com", "your-actual-domain.com"
        Set-Content $_.FullName $content
    }
    
    Print-Success "Manifests updated"
}
catch {
    Print-Error "Manifest update failed: $_"
}

# Step 9: Apply Kubernetes manifests
Print-Step "Deploying to Kubernetes..."
try {
    $KubernetesDir = Join-Path $PROJECT_ROOT "kubernetes"
    
    kubectl apply -f "$KubernetesDir/00-namespace-config.yaml"
    Start-Sleep -Seconds 2
    
    kubectl apply -f "$KubernetesDir/01-storage.yaml"
    Start-Sleep -Seconds 2
    
    kubectl apply -f "$KubernetesDir/02-backend-deployment.yaml"
    Start-Sleep -Seconds 2
    
    kubectl apply -f "$KubernetesDir/03-frontend-deployment.yaml"
    Start-Sleep -Seconds 2
    
    kubectl apply -f "$KubernetesDir/04-ingress-network.yaml"
    Start-Sleep -Seconds 2
    
    kubectl apply -f "$KubernetesDir/05-hpa.yaml"
    
    Print-Success "Deployments applied"
}
catch {
    Print-Error "Deployment failed: $_"
    exit 1
}

# Step 10: Wait for rollout
Print-Step "Waiting for deployments to be ready..."
try {
    kubectl rollout status deployment/canvas3t-backend -n $NAMESPACE
    kubectl rollout status deployment/canvas3t-frontend -n $NAMESPACE
    Print-Success "Deployments are ready"
}
catch {
    Print-Error "Rollout failed: $_"
    exit 1
}

# Step 11: Display deployment information
Write-Host ""
Print-Step "Deployment Information:"
Write-Host ""
Write-Host "Namespace: $NAMESPACE" -ForegroundColor Yellow
Write-Host "Cluster: $CLUSTER_NAME" -ForegroundColor Yellow
Write-Host "Region: $REGION" -ForegroundColor Yellow
Write-Host "AWS Account: $AWS_ACCOUNT_ID" -ForegroundColor Yellow
Write-Host ""

Write-Host "Deployments:" -ForegroundColor $Blue
kubectl get deployments -n $NAMESPACE

Write-Host ""
Write-Host "Services:" -ForegroundColor $Blue
kubectl get services -n $NAMESPACE

Write-Host ""
Write-Host "Ingress:" -ForegroundColor $Blue
kubectl get ingress -n $NAMESPACE

Write-Host ""
Write-Host "Pods:" -ForegroundColor $Blue
kubectl get pods -n $NAMESPACE

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor $Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update your DNS records to point to the ALB endpoint (see ingress EXTERNAL-IP)"
Write-Host "2. Update the SECRET_KEY in kubernetes/00-namespace-config.yaml for production"
Write-Host "3. Update VITE_API_URL in kubernetes/03-frontend-deployment.yaml"
Write-Host "4. Update yourdomain.com in kubernetes/04-ingress-network.yaml"
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  View logs: kubectl logs -f deployment/canvas3t-backend -n $NAMESPACE"
Write-Host "  Port forward: kubectl port-forward svc/canvas3t-backend 5000:5000 -n $NAMESPACE"
Write-Host "  Scale backend: kubectl scale deployment canvas3t-backend --replicas=3 -n $NAMESPACE"
Write-Host "  Get ALB DNS: kubectl get ingress canvas3t-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'"
Write-Host ""
