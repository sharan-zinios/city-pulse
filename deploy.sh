#!/bin/bash

# City Pulse Graph-RAG Deployment Script
set -e

echo "🚀 Starting City Pulse Graph-RAG deployment..."

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: PROJECT_ID environment variable is not set"
    echo "Please set it with: export PROJECT_ID=your-gcp-project-id"
    exit 1
fi

echo "📋 Using Project ID: $PROJECT_ID"

# Step 1: Deploy Infrastructure
echo "🏗️  Step 1: Deploying infrastructure with Terraform..."
cd infra
terraform init
terraform apply -var="project_id=$PROJECT_ID" -auto-approve
cd ..

# Step 2: Generate sample data
echo "📊 Step 2: Generating sample Bengaluru event data..."
cd data_gen
python3 generate.py
cd ..

# Step 3: Generate embeddings and load to BigQuery
echo "🧠 Step 3: Generating embeddings and loading to BigQuery..."
cd embed
python3 embed_and_load.py
cd ..

# Step 4: Deploy Memgraph to GKE
echo "🗄️  Step 4: Deploying Memgraph to GKE..."
gcloud container clusters get-credentials memgraph-ap --region=asia-south1
kubectl apply -f memgraph_job/memgraph-deployment.yaml
kubectl wait --for=condition=available --timeout=300s deployment/memgraph

# Step 5: Run data ingestion job
echo "📥 Step 5: Running Memgraph data ingestion job..."
envsubst < memgraph_job/job.yaml | kubectl apply -f -
kubectl wait --for=condition=complete --timeout=300s job/ingest-events

# Step 6: Deploy API to Cloud Run
echo "🌐 Step 6: Deploying API to Cloud Run..."
gcloud run deploy bengaluru-graphrag \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID

echo "✅ Deployment complete!"
echo "🔗 Your API is now available at the Cloud Run URL shown above"
echo "🧪 Test with: curl -X POST [YOUR_CLOUD_RUN_URL]/ask -H 'Content-Type: application/json' -d '{\"question\":\"What events near MG Road?\",\"lat\":12.98,\"lon\":77.60}'"
