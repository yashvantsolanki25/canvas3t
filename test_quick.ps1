#!/usr/bin/env pwsh
"""
Quick test script to verify API functionality
"""

$baseUrl = "http://localhost:5000"

# Test 1: Register user
Write-Host "=== TEST 1: Register User ===" -ForegroundColor Cyan
$userPayload = @{
    username = "testuser_$(Get-Random)"
    email = "test_$(Get-Random)@example.com"
    password = "TestPass123!"
} | ConvertTo-Json

$registerResponse = Invoke-RestMethod -Uri "$baseUrl/api/auth/register" -Method Post -Body $userPayload -ContentType "application/json"
Write-Host "Response: " -ForegroundColor Green
$registerResponse | ConvertTo-Json

$userId = $registerResponse.user_id
$username = $registerResponse.username
Write-Host "✓ User registered: ID=$userId, Username=$username" -ForegroundColor Green

# Test 2: Login and get token
Write-Host "`n=== TEST 2: Login and Get Token ===" -ForegroundColor Cyan
$loginPayload = @{
    username = $username
    password = "TestPass123!"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/auth/login" -Method Post -Body $loginPayload -ContentType "application/json"
Write-Host "Response: " -ForegroundColor Green
$loginResponse | ConvertTo-Json

$token = $loginResponse.token
Write-Host "✓ Token obtained: $($token.Substring(0, 20))..." -ForegroundColor Green

# Test 3: Upload image
Write-Host "`n=== TEST 3: Upload Image ===" -ForegroundColor Cyan

# Create a simple test image (1x1 PNG)
$pngBytes = [byte[]]@(
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
    0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8, 0x0F, 0x00, 0x00,
    0x01, 0x01, 0x00, 0x03, 0x52, 0x9E, 0xF4, 0xDC, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,
    0xAE, 0x42, 0x60, 0x82
)

$tempImagePath = [System.IO.Path]::GetTempFileName()
$tempImagePath = $tempImagePath -replace '\.tmp$', '.png'
[System.IO.File]::WriteAllBytes($tempImagePath, $pngBytes)

$headers = @{
    Authorization = "Bearer $token"
}

$form = @{
    title = "Test Upload"
    is_public = "false"
    tags = "test"
    user_id = $userId
}

try {
    $uploadResponse = Invoke-RestMethod -Uri "$baseUrl/api/paintings" -Method Post -Form $form -Headers $headers -ContentType "multipart/form-data"
    Write-Host "Upload failed - form not working correctly"
} catch {
    # Fallback: Use curl
    Write-Host "Using curl for upload..."
    $curlCmd = "curl -s -X POST $baseUrl/api/paintings -H `"Authorization: Bearer $token`" -F `"image=@$tempImagePath`" -F `"title=Test Upload`" -F `"is_public=false`" -F `"tags=test`" | ConvertFrom-Json"
    $uploadResponse = Invoke-Expression $curlCmd
}

Write-Host "Response: " -ForegroundColor Green
$uploadResponse | ConvertTo-Json

if ($uploadResponse.painting) {
    $paintingId = $uploadResponse.painting.id
    Write-Host "✓ Image uploaded: ID=$paintingId" -ForegroundColor Green
} else {
    Write-Host "✗ Upload failed" -ForegroundColor Red
}

# Cleanup
Remove-Item $tempImagePath -Force -ErrorAction SilentlyContinue

# Test 4: List paintings
Write-Host "`n=== TEST 4: List Paintings ===" -ForegroundColor Cyan
$listResponse = Invoke-RestMethod -Uri "$baseUrl/api/paintings?user_id=$userId" -Method Get -Headers $headers
Write-Host "Response: " -ForegroundColor Green
$listResponse | ConvertTo-Json -Depth 2

Write-Host "✓ Total paintings: $($listResponse.total)" -ForegroundColor Green

Write-Host "`n=== ALL TESTS COMPLETED ===" -ForegroundColor Green
