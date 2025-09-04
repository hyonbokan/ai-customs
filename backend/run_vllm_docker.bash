#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Get the absolute path of the directory where this script is located.
# This makes the script runnable from any directory.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# --- 1. Setup Docker Network ---
# We create a user-defined bridge network. Containers on the same network
# can discover and communicate with each other by their container name.
echo "Creating Docker network 'ai-net'..."
sudo docker network create ai-net || true

# --- 2. Stop and Remove Old Containers ---
# This ensures we don't have conflicts from previous runs.
echo "Stopping and removing old containers if they exist..."
sudo docker rm -f vllm || true
sudo docker rm -f customs-ai-container || true

# --- 3. Build the Backend Docker Image ---
# This step rebuilds the image for the backend service, including any
# recent code changes. We explicitly provide the path to the Dockerfile
# and the build context directory to avoid ambiguity.
echo "Building the AI Customs backend Docker image..."
sudo docker build -t customs-ai-backend -f "$SCRIPT_DIR/Dockerfile" "$SCRIPT_DIR"

# --- 4. Start the vLLM Container ---
# We start the vLLM model server and attach it to our network.
# It is named 'vllm', which is how our backend will find it.
echo "Starting vLLM container in the background..."
sudo docker run -d --gpus all \
  --name vllm \
  --network ai-net \
  --restart unless-stopped \
  -v /home/dnlab/models:/models \
  -p 8080:80 \
  --shm-size=2g \
  vllm/vllm-openai:latest \
  --model /models/gemma-3-27b-it \
  --dtype auto \
  --port 80 \
  --tensor-parallel-size 2

# --- 5. Wait for vLLM to be Healthy ---
echo "Waiting for vLLM container to be healthy. This can take several minutes..."
end_time=$((SECONDS+300)) # n-second timeout

while [ $SECONDS -lt $end_time ]; do
  if curl -sS --fail http://localhost:8080/health > /dev/null 2>&1; then
    echo "vLLM is healthy and ready to accept requests!"
    break
  fi
  echo -n "."
  sleep 5
done

if ! curl -sS --fail http://localhost:8080/health > /dev/null 2>&1; then
  echo -e "\nError: vLLM container did not become healthy within 5 minutes."
  echo "Displaying vLLM logs for debugging:"
  sudo docker logs vllm | tail -n 200
  exit 1
fi


# --- 6. Start the AI Customs Backend Container ---
# Now that vLLM is confirmed ready, we start the backend.
echo "Starting AI Customs backend container..."
sudo docker run -d \
  --name customs-ai-container \
  --network ai-net \
  -p 8000:8000 \
  -e LLM_BASE_URL=http://vllm:80/v1/ \
  customs-ai-backend

# --- 7. Verify and Test ---
echo "Waiting for backend service to start..."
sleep 15 # Give the backend a moment to initialize

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
