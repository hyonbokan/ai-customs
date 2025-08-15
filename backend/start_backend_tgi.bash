#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- 1. Setup Docker Network ---
# We create a user-defined bridge network. Containers on the same network
# can discover and communicate with each other by their container name.
echo "Creating Docker network 'ai-net'..."
sudo docker network create ai-net || true

# --- 2. Stop and Remove Old Containers ---
# This ensures we don't have conflicts from previous runs.
echo "Stopping and removing old containers if they exist..."
sudo docker rm -f tgi || true
sudo docker rm -f customs-ai-container || true

# --- 3. Start the TGI Container ---
# We start the TGI model server and attach it to our network.
# It is named 'tgi', which is how our backend will find it.
echo "Starting TGI container..."
sudo docker run -d --gpus all \
  --name tgi \
  --network ai-net \
  -v ~/models/gemma-3-27b-it:/models/gemma-3-27b-it \
  -p 8080:80 \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id /models/gemma-3-27b-it --trust-remote-code --num-shard 2

# --- 4. Start the AI Customs Backend Container ---
# We start the backend application, attach it to the same network,
# and tell it where to find the TGI service using the container name.
echo "Starting AI Customs backend container..."
sudo docker run -d \
  --name customs-ai-container \
  --network ai-net \
  -p 8000:8000 \
  -e TGI_BASE_URL=http://tgi:80/v1/ \
  customs-ai-backend

# --- 5. Verify and Test ---
echo "Waiting for services to start..."
sleep 15 # Give the containers a moment to initialize

echo "Verifying containers are running..."
sudo docker ps

echo -e "\n--- Testing API Endpoint ---"
curl -X POST http://localhost:8000/api/v1/analyze-declaration \
-H "Content-Type: application/json" \
-d '{
  "declaration_data": {
    "declaration_number": "VERIFY-001", "importer": "Test Client",
    "goods": [{"description": "Test Goods", "value": 100}], "total_value": 100
  }
}'

echo -e "\n\nSetup complete. Both containers are running and connected."