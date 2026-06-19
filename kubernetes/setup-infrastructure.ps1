# EKS Infrastructure Setup Script

# This script sets up all the necessary AWS infrastructure for EKS deployment

param(
    [string]$CLUSTER_NAME = "canvas3t-cluster",
    [string]$REGION = "us-east-1",
    [string]$NODE_TYPE = "t3.medium",
    [int]$NODE_COUNT = 2,
    [string]$K8S_VERSION = "1.28"
)

# Colors for output
$Green = 'Green'
$Red = 'Red'
$Yellow = 'Yellow'
$Cyan = 'Cyan'

function Print-Step {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor $Cyan
}

function Print-Success {
    param([string]$Message)
    Write-Host "[+] $Message" -ForegroundColor $Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "[-] $Message" -ForegroundColor $Red
}

function Print-Warning {
    param([string]$Message)
    Write-Host "[!] $Message" -ForegroundColor $Yellow
}

Clear-Host
Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor $Cyan
Write-Host "║   EKS Infrastructure Setup Script         ║" -ForegroundColor $Cyan
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor $Cyan
Write-Host ""

# Step 1: Verify prerequisites
Print-Step "Verifying prerequisites..."

$tools = @("aws", "kubectl", "eksctl", "docker")
$missing = @()

foreach ($tool in $tools) {
    try {
        $result = & $tool --version 2>$null
        Print-Success "$tool is installed"
    }
    catch {
        $missing += $tool
        Print-Error "$tool is NOT installed"
    }
}

if ($missing.Count -gt 0) {
    Print-Error "Missing tools: $($missing -join ', ')"
    Write-Host ""
    Write-Host "Install missing tools with:" -ForegroundColor $Yellow
    Write-Host "choco install $($missing -join ' ')" -ForegroundColor $Cyan
    exit 1
}

Print-Success "All prerequisites verified"
Write-Host ""

# Step 2: Configure AWS
Print-Step "Configuring AWS..."

try {
    $identity = aws sts get-caller-identity | ConvertFrom-Json
    Print-Success "AWS credentials configured"
    Print-Success "Account: $($identity.Account)"
    Print-Success "User: $($identity.Arn)"
    $AWS_ACCOUNT_ID = $identity.Account
}
catch {
    Print-Error "AWS credentials not configured"
    Write-Host "Run: aws configure" -ForegroundColor $Yellow
    exit 1
}

Write-Host ""

# Step 3: Create EKS Cluster
Print-Step "Creating EKS cluster: $CLUSTER_NAME"
Print-Warning "This will take 15-20 minutes..."

try {
    eksctl create cluster `
        --name $CLUSTER_NAME `
        --region $REGION `
        --version $K8S_VERSION `
        --nodegroup-name "${CLUSTER_NAME}-nodes" `
        --node-type $NODE_TYPE `
        --nodes $NODE_COUNT `
        --nodes-min 1 `
        --nodes-max 4 `
        --managed `
        --enable-ssm

    Print-Success "EKS cluster created successfully"
}
catch {
    Print-Error "Failed to create EKS cluster: $_"
    exit 1
}

Write-Host ""

# Step 4: Verify cluster
Print-Step "Verifying cluster setup..."

try {
    $nodes = kubectl get nodes
    Print-Success "Cluster is accessible"
    Write-Host $nodes
}
catch {
    Print-Error "Cannot access cluster"
    exit 1
}

Write-Host ""

# Step 5: Install metrics-server
Print-Step "Installing metrics-server for monitoring..."

try {
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    Start-Sleep -Seconds 5
    kubectl wait --for=condition=ready pod -l k8s-app=metrics-server -n kube-system --timeout=60s 2>$null
    Print-Success "metrics-server installed"
}
catch {
    Print-Warning "Could not install metrics-server (non-critical)"
}

Write-Host ""

# Step 6: Install AWS Load Balancer Controller
Print-Step "Installing AWS Load Balancer Controller..."

try {
    # Add helm repo
    helm repo add eks https://aws.github.io/eks-charts
    helm repo update

    # Install ALB controller
    helm install aws-load-balancer-controller eks/aws-load-balancer-controller `
        -n kube-system `
        --set clusterName=$CLUSTER_NAME

    Print-Success "AWS Load Balancer Controller installed"
}
catch {
    Print-Warning "Could not install ALB controller. You may need to do this manually."
    Write-Host "See: https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html" -ForegroundColor $Yellow
}

Write-Host ""

# Step 7: Create namespaces
Print-Step "Setting up Kubernetes resources..."

try {
    kubectl create namespace canvas3t 2>$null
    kubectl label namespace canvas3t environment=production 2>$null
    Print-Success "Namespace 'canvas3t' created"
}
catch {
    Print-Warning "Namespace may already exist"
}

Write-Host ""

# Step 8: Create IAM policy for ALB (if needed)
Print-Step "Setting up IAM policies..."

try {
    # Create IAM role policy for ALB
    $policy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "elbv2:CreateLoadBalancer",
        "elbv2:CreateTargetGroup",
        "elbv2:DescribeLoadBalancers",
        "elbv2:DescribeTargetGroups",
        "elbv2:CreateListener",
        "elbv2:ModifyListener",
        "elbv2:CreateRule",
        "elbv2:ModifyRule",
        "elbv2:DescribeRules",
        "elbv2:DescribeListeners"
      ],
      "Resource": "*"
    }
  ]
}
"@

    Print-Success "IAM policies prepared"
}
catch {
    Print-Warning "Could not prepare IAM policies (non-critical)"
}

Write-Host ""

# Step 9: Create ECR repositories
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

    Print-Success "ECR repositories created"
}
catch {
    Print-Warning "ECR repositories may already exist"
}

Write-Host ""

# Step 10: Display summary
Print-Step "Setup Summary"
Write-Host ""
Write-Host "Cluster Configuration:" -ForegroundColor $Cyan
Write-Host "  Name: $CLUSTER_NAME" -ForegroundColor $Yellow
Write-Host "  Region: $REGION" -ForegroundColor $Yellow
Write-Host "  Kubernetes Version: $K8S_VERSION" -ForegroundColor $Yellow
Write-Host "  Node Type: $NODE_TYPE" -ForegroundColor $Yellow
Write-Host "  Initial Node Count: $NODE_COUNT" -ForegroundColor $Yellow
Write-Host "  AWS Account: $AWS_ACCOUNT_ID" -ForegroundColor $Yellow
Write-Host ""

Write-Host "ECR Repositories:" -ForegroundColor $Cyan
Write-Host "  Backend: $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/canvas3t-backend" -ForegroundColor $Yellow
Write-Host "  Frontend: $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/canvas3t-frontend" -ForegroundColor $Yellow
Write-Host ""

Write-Host "Kubernetes Namespace:" -ForegroundColor $Cyan
Write-Host "  Name: canvas3t" -ForegroundColor $Yellow
Write-Host ""

# Step 11: Display next steps
Write-Host "✓ Infrastructure setup completed!" -ForegroundColor $Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor $Cyan
Write-Host "1. Update Kubernetes manifests with your AWS Account ID" -ForegroundColor $Yellow
Write-Host "   sed 's/YOUR_AWS_ACCOUNT_ID/$AWS_ACCOUNT_ID/g' kubernetes/*.yaml" -ForegroundColor $Cyan
Write-Host ""
Write-Host "2. Build and push Docker images" -ForegroundColor $Yellow
Write-Host "   .\kubernetes\deploy.ps1" -ForegroundColor $Cyan
Write-Host ""
Write-Host "3. Verify cluster status" -ForegroundColor $Yellow
Write-Host "   kubectl get nodes" -ForegroundColor $Cyan
Write-Host "   kubectl get pods -A" -ForegroundColor $Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor $Cyan
Write-Host "  View cluster info: aws eks describe-cluster --name $CLUSTER_NAME --region $REGION" -ForegroundColor $Cyan
Write-Host "  Scale node group: aws eks update-nodegroup-config --cluster-name $CLUSTER_NAME --nodegroup-name ${CLUSTER_NAME}-nodes --scaling-config minSize=1,maxSize=4,desiredSize=3 --region $REGION" -ForegroundColor $Cyan
Write-Host "  Delete cluster: eksctl delete cluster --name $CLUSTER_NAME --region $REGION" -ForegroundColor $Cyan
Write-Host ""

Print-Success "All done! 🎉"
