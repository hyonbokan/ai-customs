#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[TGI-ENTRYPOINT]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[TGI-WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[TGI-ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[TGI-INFO]${NC} $1"
}

# Function to detect GPU configuration with field-tested improvements
detect_gpu_config() {
    log "Detecting GPU configuration..."
    
    # Check if nvidia-smi is available
    if ! command -v nvidia-smi &> /dev/null; then
        warn "nvidia-smi not found, assuming CPU mode"
        export TGI_NUM_SHARD="1"
        return 0
    fi
    
    # Check if nvidia-smi works (addresses NVML initialization issue)
    if ! nvidia-smi > /dev/null 2>&1; then
        error "nvidia-smi failed to initialize NVML"
        error "This usually indicates a driver/runtime mismatch"
        warn "Falling back to CPU mode"
        export TGI_NUM_SHARD="1"
        return 0
    fi
    
    # Get GPU count and information
    local gpu_count=$(nvidia-smi --list-gpus | wc -l)
    if [ "$gpu_count" -eq 0 ]; then
        warn "No GPUs detected, running in CPU mode"
        export TGI_NUM_SHARD="1"
        return 0
    fi
    
    info "Found $gpu_count GPU(s)"
    
    # Display detailed GPU information
    nvidia-smi --query-gpu=index,name,memory.total,memory.free,temperature.gpu,utilization.gpu --format=csv,noheader,nounits | while IFS=, read -r index name total_mem free_mem temp util; do
        info "  GPU $index: $name - ${total_mem}MB total, ${free_mem}MB free, ${temp}°C, ${util}% util"
    done
    
    # Auto-configure shards based on GPU count and memory
    if [ "$TGI_NUM_SHARD" = "auto" ]; then
        # Field-tested heuristic: 
        # - For models >20GB: use all GPUs
        # - For smaller models: use fewer shards to avoid overhead
        local total_vram=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | awk '{sum += $1} END {print sum}')
        local avg_vram_per_gpu=$((total_vram / gpu_count))
        
        if [ "$avg_vram_per_gpu" -gt 20000 ]; then
            # High-memory GPUs: use all for large models
            export TGI_NUM_SHARD="$gpu_count"
        elif [ "$gpu_count" -gt 4 ]; then
            # Many GPUs: limit to 4 to avoid communication overhead
            export TGI_NUM_SHARD="4"
        else
            # Use all available GPUs
            export TGI_NUM_SHARD="$gpu_count"
        fi
        
        info "Auto-configured shards: $TGI_NUM_SHARD (based on ${gpu_count} GPUs with ${avg_vram_per_gpu}MB each)"
    else
        # Validate manual shard configuration
        if [ "$TGI_NUM_SHARD" -gt "$gpu_count" ]; then
            warn "TGI_NUM_SHARD ($TGI_NUM_SHARD) > available GPUs ($gpu_count)"
            warn "Limiting to available GPU count"
            export TGI_NUM_SHARD="$gpu_count"
        fi
        info "Using manually configured shards: $TGI_NUM_SHARD"
    fi
    
    # Check for common GPU issues
    local gpu_errors=$(nvidia-smi --query-gpu=gpu_bus_id,retired_pages.pending,temperature.gpu --format=csv,noheader | grep -E "Yes|[0-9][0-9][0-9]" | wc -l)
    if [ "$gpu_errors" -gt 0 ]; then
        warn "Some GPUs may have issues (pending retired pages or high temperature)"
        warn "Monitor GPU health during operation"
    fi
    
    return 0
}

# Function to find model directory with improved logic
find_model_path() {
    local base_path="$MODEL_PATH"
    
    info "Looking for model in: $base_path"
    
    # Check if specific model directory exists
    if [ ! -d "$base_path" ]; then
        error "Model base path does not exist: $base_path"
        return 1
    fi
    
    # Look for config.json to identify the actual model directory
    local config_files=$(find "$base_path" -name "config.json" -type f 2>/dev/null)
    
    if [ -z "$config_files" ]; then
        error "No config.json found in $base_path"
        error "Make sure the model is properly downloaded and mounted"
        return 1
    fi
    
    # If multiple config.json files, use the first one (most likely the model)
    local model_dir=$(echo "$config_files" | head -1 | xargs dirname)
    
    if [ -n "$model_dir" ] && [ -d "$model_dir" ]; then
        echo "$model_dir"
        return 0
    fi
    
    return 1
}

# Function to validate model with comprehensive checks
validate_model() {
    local model_path="$1"
    
    log "Validating model at: $model_path"
    
    # Check if directory exists
    if [ ! -d "$model_path" ]; then
        error "Model directory does not exist: $model_path"
        return 1
    fi
    
    # Check essential files with better error reporting
    local essential_files=("config.json" "tokenizer.json")
    local missing_files=()
    
    for file in "${essential_files[@]}"; do
        if [ ! -f "$model_path/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        error "Missing essential files: ${missing_files[*]}"
        error "Model appears to be incomplete or corrupted"
        return 1
    fi
    
    # Check for model weights with better detection
    local weight_files=$(find "$model_path" -name "*.safetensors" -o -name "*.bin" 2>/dev/null | wc -l)
    if [ "$weight_files" -eq 0 ]; then
        error "No model weights found (*.safetensors or *.bin)"
        error "Model download may be incomplete"
        return 1
    fi
    
    # Check total model size
    local total_size=$(du -sh "$model_path" 2>/dev/null | cut -f1)
    info "Model size: $total_size"
    
    # Check for tokenizer files
    local tokenizer_files=("tokenizer.json" "tokenizer_config.json")
    for file in "${tokenizer_files[@]}"; do
        if [ -f "$model_path/$file" ]; then
            info "Found tokenizer file: $file"
        else
            warn "Missing tokenizer file: $file (may cause issues)"
        fi
    done
    
    # Check model configuration
    if [ -f "$model_path/config.json" ]; then
        local model_type=$(grep -o '"model_type"[[:space:]]*:[[:space:]]*"[^"]*"' "$model_path/config.json" | cut -d'"' -f4)
        local vocab_size=$(grep -o '"vocab_size"[[:space:]]*:[[:space:]]*[0-9]*' "$model_path/config.json" | grep -o '[0-9]*$')
        
        if [ -n "$model_type" ]; then
            info "Model type: $model_type"
        fi
        if [ -n "$vocab_size" ]; then
            info "Vocabulary size: $vocab_size"
        fi
    fi
    
    info "Model validation passed"
    return 0
}

# Function to build TGI command with field-tested parameters
build_tgi_command() {
    local model_path="$1"
    
    log "Building TGI command with optimized parameters..."
    
    local cmd=(
        "text-generation-launcher"
        "--model-id" "$model_path"
        "--host" "$TGI_HOST"
        "--port" "$TGI_PORT"
        "--num-shard" "$TGI_NUM_SHARD"
    )
    
    # Add performance parameters
    cmd+=("--max-concurrent-requests" "$TGI_MAX_CONCURRENT_REQUESTS")
    cmd+=("--max-best-of" "$TGI_MAX_BEST_OF")
    cmd+=("--max-stop-sequences" "$TGI_MAX_STOP_SEQUENCES")
    cmd+=("--max-input-length" "$TGI_MAX_INPUT_LENGTH")
    cmd+=("--max-total-tokens" "$TGI_MAX_TOTAL_TOKENS")
    cmd+=("--waiting-served-ratio" "$TGI_WAITING_SERVED_RATIO")
    cmd+=("--max-batch-prefill-tokens" "$TGI_MAX_BATCH_PREFILL_TOKENS")
    cmd+=("--max-batch-total-tokens" "$TGI_MAX_BATCH_TOTAL_TOKENS")
    
    # Add trust-remote-code if enabled
    if [ "$TGI_TRUST_REMOTE_CODE" = "true" ]; then
        cmd+=("--trust-remote-code")
    fi
    
    # Add JSON schema support if available
    cmd+=("--json-schema" "true")
    
    # Memory optimization for large models
    if [ "$TGI_NUM_SHARD" -gt 1 ]; then
        cmd+=("--dtype" "float16")  # Use float16 for multi-GPU setups
    fi
    
    echo "${cmd[@]}"
}

# Function to perform pre-flight checks
preflight_checks() {
    log "Performing pre-flight checks..."
    
    # Check CUDA_VISIBLE_DEVICES
    if [ -n "$CUDA_VISIBLE_DEVICES" ] && [ "$CUDA_VISIBLE_DEVICES" != "all" ]; then
        info "CUDA_VISIBLE_DEVICES set to: $CUDA_VISIBLE_DEVICES"
        
        # Validate GPU indices
        local available_gpus=$(nvidia-smi --list-gpus | wc -l)
        local requested_gpus=$(echo "$CUDA_VISIBLE_DEVICES" | tr ',' '\n' | wc -l)
        
        if [ "$requested_gpus" -gt "$available_gpus" ]; then
            warn "⚠️  CUDA_VISIBLE_DEVICES specifies more GPUs than available"
        fi
    fi
    
    # Check disk space in cache directory
    if [ -d "/opt/cache" ]; then
        local cache_space=$(df -BG /opt/cache 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/G//' || echo "0")
        if [ "$cache_space" -lt 10 ]; then
            warn "⚠️  Low disk space in cache directory: ${cache_space}GB"
        fi
    fi
    
    # Check system memory
    local total_mem=$(free -g | awk '/^Mem:/{print $2}')
    local free_mem=$(free -g | awk '/^Mem:/{print $7}')
    info "💾 System memory: ${free_mem}GB free / ${total_mem}GB total"
    
    if [ "$free_mem" -lt 8 ]; then
        warn "⚠️  Low system memory: ${free_mem}GB free"
        warn "Consider reducing concurrent requests or batch size"
    fi
    
    return 0
}

# Function to setup logging and monitoring
setup_logging() {
    # Create log directory
    mkdir -p /var/log/tgi
    
    # Set up log rotation
    if [ -f "/var/log/tgi/tgi.log" ]; then
        # Keep last 3 log files
        for i in 2 1 0; do
            if [ -f "/var/log/tgi/tgi.log.$i" ]; then
                mv "/var/log/tgi/tgi.log.$i" "/var/log/tgi/tgi.log.$((i+1))"
            fi
        done
        mv "/var/log/tgi/tgi.log" "/var/log/tgi/tgi.log.0"
    fi
    
    # Set log level
    export RUST_LOG="${RUST_LOG:-info}"
    
    info "📝 Logging configured - Level: $RUST_LOG"
}

# Main execution
main() {
    log "🚀 Starting TGI Entrypoint (Field-Tested Version)..."
    
    # Setup logging
    setup_logging
    
    # Perform pre-flight checks
    preflight_checks
    
    # Detect GPU configuration
    detect_gpu_config
    
    # Find model path
    if ! model_path=$(find_model_path); then
        error "❌ Failed to find model"
        error "📋 Troubleshooting steps:"
        error "  1. Ensure model is properly downloaded"
        error "  2. Check volume mount: -v /host/path:/opt/models"
        error "  3. Verify model contains config.json"
        error "  4. Check permissions: should be readable by user 1000"
        exit 1
    fi
    
    log "✅ Found model at: $model_path"
    
    # Validate model
    if ! validate_model "$model_path"; then
        error "❌ Model validation failed"
        error "📋 Common solutions:"
        error "  1. Re-download the model"
        error "  2. Check for sufficient disk space during download"
        error "  3. Verify model is compatible with TGI"
        exit 1
    fi
    
    # Build and display command
    tgi_cmd=$(build_tgi_command "$model_path")
    
    log "🎯 TGI Configuration:"
    log "  Model: $model_path"
    log "  Shards: $TGI_NUM_SHARD"
    log "  Host: $TGI_HOST:$TGI_PORT"
    log "  Max Concurrent: $TGI_MAX_CONCURRENT_REQUESTS"
    log "  Max Input Length: $TGI_MAX_INPUT_LENGTH"
    log "  Max Total Tokens: $TGI_MAX_TOTAL_TOKENS"
    
    info "🚀 Starting TGI with command:"
    info "$tgi_cmd"
    
    # Start TGI with proper signal handling
    log "🎬 Launching Text Generation Inference..."
    
    # Use exec to replace the shell process (proper signal handling)
    exec $tgi_cmd
}

# Handle signals gracefully
trap 'log "🛑 Received termination signal, shutting down..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@" 