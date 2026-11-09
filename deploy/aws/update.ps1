# update.ps1 - ship a new latin-morph image to Lambda (see deploy/aws/README.md)
#   powershell -ExecutionPolicy Bypass -File deploy\aws\update.ps1 -Key C:\path\to\n8n-key.pem
param(
  [Parameter(Mandatory = $true)][string]$Key,         # SSH key of the arm64 build host
  [string]$BuildHost = "ec2-user@52.13.126.20",       # n8n EC2 (arm64), used only to build
  [string]$Region = "us-west-2",
  [string]$Function = "latin-morph",
  [string]$Distribution = "E2YUMSVB9GGHRW"
)
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$account = (aws sts get-caller-identity --query Account --output text).Trim()
$registry = "$account.dkr.ecr.$Region.amazonaws.com"
$ver = (Select-String -Path "$root\skills\latin-morphology\scripts\latin_morph\__init__.py" -Pattern '__version__\s*=\s*"([^"]+)"').Matches[0].Groups[1].Value
$tag = "$ver-" + (Get-Date -Format "yyyyMMddHHmm")
$image = "$registry/latin-morph:$tag"
$ssh = @("-i", $Key, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes")

Write-Host "==> source -> $BuildHost" -ForegroundColor Cyan
$tgz = Join-Path $env:TEMP "latin-src.tgz"
tar -C $root --exclude=.git --exclude=__pycache__ -czf $tgz Dockerfile .dockerignore requirements-server.txt skills server
scp @ssh -q $tgz "${BuildHost}:/tmp/latin-src.tgz"

Write-Host "==> build + push $image" -ForegroundColor Cyan
$remote = "set -e; rm -rf ~/latin-build; mkdir ~/latin-build; tar -xzf /tmp/latin-src.tgz -C ~/latin-build; " +
          "cd ~/latin-build; docker build -q --provenance=false -t $image .; " +
          "docker login --username AWS --password-stdin $registry >/dev/null; " +
          "docker push -q $image; docker logout $registry >/dev/null; rm -rf ~/latin-build /tmp/latin-src.tgz"
aws ecr get-login-password --region $Region | ssh @ssh $BuildHost $remote
if ($LASTEXITCODE -ne 0) { throw "build/push failed" }

Write-Host "==> Lambda $Function -> $tag" -ForegroundColor Cyan
aws lambda update-function-code --region $Region --function-name $Function --image-uri $image --query LastUpdateStatus --output text
aws lambda wait function-updated-v2 --region $Region --function-name $Function

Write-Host "==> CloudFront invalidation" -ForegroundColor Cyan
aws cloudfront create-invalidation --distribution-id $Distribution --paths "/*" --query Invalidation.Id --output text

Write-Host "==> /health" -ForegroundColor Cyan
Invoke-RestMethod "https://latin.diodorus.com.br/health" -TimeoutSec 40 | ConvertTo-Json -Compress
