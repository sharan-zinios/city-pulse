# City Pulse Graph-RAG Deployment Script (PowerShell)
# Equivalent of deploy.sh
$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting City Pulse Graph-RAG deployment..." -ForegroundColor Green

# 1. Check PROJECT_ID
if (-not $env:PROJECT_ID) {
    Write-Host "❌ Error: PROJECT_ID environment variable is not set" -ForegroundColor Red
    Write-Host "Please set it with: `$env:PROJECT_ID = 'your-gcp-project-id'" -ForegroundColor Yellow
    exit 1
}
Write-Host "📋 Using Project ID: $($env:PROJECT_ID)" -ForegroundColor Cyan

# 2. Terraform infrastructure
Write-Host "🏗️  Step 1: Deploying infrastructure with Terraform..." -ForegroundColor Blue
Push-Location infra
terraform init
terraform apply -var="project_id=$($env:PROJECT_ID)" -auto-approve
Pop-Location

# 3. Generate sample data
Write-Host "📊 Step 2: Generating sample Bengaluru event data..." -ForegroundColor Blue
Push-Location data_gen
python generate.py
Pop-Location

# 4. Generate embeddings & load to BigQuery
Write-Host "🧠 Step 3: Generating embeddings and loading to BigQuery..." -ForegroundColor Blue
Push-Location embed
python embed_and_load.py
Pop-Location

# 5. Deploy Memgraph to GKE
Write-Host "🗄️  Step 4: Deploying Memgraph to GKE..." -ForegroundColor Blue
gcloud container clusters get-credentials memgraph-ap --region=asia-south1
kubectl apply -f memgraph_job/memgraph-deployment.yaml
kubectl wait --for=condition=available --timeout=300s deployment/memgraph

# 6. Run data-ingestion job (envsubst replacement)
Write-Host "📥 Step 5: Running Memgraph data ingestion job..." -ForegroundColor Blue
$jobYaml = Get-Content memgraph_job/job.yaml -Raw
$jobYaml = $jobYaml -replace '\$\{PROJECT_ID\}', $env:PROJECT_ID
$jobYaml | kubectl apply -f -
kubectl wait --for=condition=complete --timeout=300s job/ingest-events

# 7. Deploy API to Cloud Run
Write-Host "🌐 Step 6: Deploying API to Cloud Run..." -ForegroundColor Blue
gcloud run deploy bengaluru-graphrag `
  --source . `
  --region asia-south1 `
  --allow-unauthenticated `
  --set-env-vars "PROJECT_ID=$($env:PROJECT_ID)"

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🔗 Your API is now available at the Cloud Run URL shown above"
Write-Host 'Test with: curl -X POST [YOUR_CLOUD_RUN_URL]/ask -H "Content-Type: application/json" -d "{\"question\":\"What events near MG Road?\",\"lat\":12.98,\"lon\":77.60}"'