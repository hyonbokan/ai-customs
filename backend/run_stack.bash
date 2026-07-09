#!/usr/bin/env bash
#
# Bring up the LLM inference server (vLLM or TGI) and the AI Customs backend,
# wired together on a private Docker network.
#
# vLLM is the primary serving engine; TGI is kept for comparison.
#
# Usage:
#   ./run_stack.bash            # defaults to vllm
#   ./run_stack.bash vllm       # serve the model with vLLM (default)
#   ./run_stack.bash tgi        # serve the model with Text Generation Inference
#
# Configuration (override via environment variables):
#   MODEL_DIR       Host directory holding the model    (default: ~/models/gemma-3-27b-it)
#   MODEL_NAME      Model name as seen inside the server (default: gemma-3-27b-it)
#   NUM_GPUS        Tensor-parallel / shard count        (default: 2)
#   LLM_PORT        Host port for the model server       (default: 8080)
#   BACKEND_PORT    Host port for the backend            (default: 8000)
#   NETWORK         Docker network name                  (default: ai-net)
#   HEALTH_TIMEOUT  Seconds to wait for services         (default: 600)
#   DOCKER          Docker command                       (default: "sudo docker")

set -euo pipefail

ENGINE="${1:-vllm}"
if [[ "$ENGINE" != "tgi" && "$ENGINE" != "vllm" ]]; then
    echo "Usage: $0 [vllm|tgi]  (default: vllm)" >&2
    exit 2
fi

# --- Configuration --------------------------------------------------------
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
MODEL_DIR="${MODEL_DIR:-$HOME/models/gemma-3-27b-it}"
MODEL_NAME="${MODEL_NAME:-gemma-3-27b-it}"
NUM_GPUS="${NUM_GPUS:-2}"
LLM_PORT="${LLM_PORT:-8080}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
NETWORK="${NETWORK:-ai-net}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-600}"
DOCKER="${DOCKER:-sudo docker}"

BACKEND_IMAGE="customs-ai-backend"
BACKEND_CONTAINER="customs-ai-container"
LLM_CONTAINER="$ENGINE"

# --- Helpers --------------------------------------------------------------
wait_for_healthy() {
    # wait_for_healthy <name> <url> <timeout_seconds> <container>
    local name="$1" url="$2" timeout="$3" container="$4"
    echo "Waiting for $name to become healthy (timeout: ${timeout}s)..."
    local deadline=$((SECONDS + timeout))
    while (( SECONDS < deadline )); do
        if curl -sS --fail "$url" > /dev/null 2>&1; then
            echo "$name is healthy."
            return 0
        fi
        printf '.'
        sleep 5
    done
    echo -e "\nError: $name did not become healthy within ${timeout}s. Recent logs:" >&2
    $DOCKER logs --tail 200 "$container" >&2 || true
    exit 1
}

# --- 1. Network -----------------------------------------------------------
echo "Ensuring Docker network '$NETWORK' exists..."
$DOCKER network create "$NETWORK" 2> /dev/null || true

# --- 2. Clean up old containers -------------------------------------------
echo "Removing any existing containers..."
$DOCKER rm -f "$LLM_CONTAINER" "$BACKEND_CONTAINER" 2> /dev/null || true

# --- 3. Build the backend image -------------------------------------------
echo "Building the AI Customs backend image..."
$DOCKER build -t "$BACKEND_IMAGE" -f "$SCRIPT_DIR/Dockerfile" "$SCRIPT_DIR"

# --- 4. Start the model server --------------------------------------------
echo "Starting $ENGINE container..."
if [[ "$ENGINE" == "tgi" ]]; then
    $DOCKER run -d --gpus all \
        --name "$LLM_CONTAINER" \
        --network "$NETWORK" \
        --restart unless-stopped \
        -v "$MODEL_DIR:/models/$MODEL_NAME" \
        -p "$LLM_PORT:80" \
        ghcr.io/huggingface/text-generation-inference:latest \
        --model-id "/models/$MODEL_NAME" --trust-remote-code --num-shard "$NUM_GPUS"
else
    $DOCKER run -d --gpus all \
        --name "$LLM_CONTAINER" \
        --network "$NETWORK" \
        --restart unless-stopped \
        --shm-size=2g \
        -v "$MODEL_DIR:/models/$MODEL_NAME" \
        -p "$LLM_PORT:80" \
        vllm/vllm-openai:latest \
        --model "/models/$MODEL_NAME" --served-model-name "$MODEL_NAME" \
        --dtype auto --port 80 --tensor-parallel-size "$NUM_GPUS"
fi

wait_for_healthy "$ENGINE" "http://localhost:$LLM_PORT/health" "$HEALTH_TIMEOUT" "$LLM_CONTAINER"

# --- 5. Start the backend -------------------------------------------------
echo "Starting AI Customs backend container..."
$DOCKER run -d \
    --name "$BACKEND_CONTAINER" \
    --network "$NETWORK" \
    -p "$BACKEND_PORT:8000" \
    -e "LLM_BASE_URL=http://$LLM_CONTAINER:80/v1/" \
    "$BACKEND_IMAGE"

wait_for_healthy "backend" "http://localhost:$BACKEND_PORT/api/v1/health-check" 60 "$BACKEND_CONTAINER"

# --- 6. Done --------------------------------------------------------------
$DOCKER ps
echo
echo "Stack is up. Try it:"
echo "  curl -X POST http://localhost:$BACKEND_PORT/api/v1/analyze-declaration \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d @$SCRIPT_DIR/request_body_examples/declaration_analysis.json"
