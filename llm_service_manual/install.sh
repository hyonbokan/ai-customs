#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[TGI-INSTALL]${NC} $1"
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

# Configuration
DEFAULT_MODEL="google/gemma-3-27b-it"
DEFAULT_MODEL_DIR="./models"
REQUIRED_DISK_SPACE_GB=60

# Function to show usage
show_usage() {
    cat << EOF
TGI Installation Script - Field-Tested & Hardened

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -m, --model-id MODEL    Model ID to download (default: $DEFAULT_MODEL)
    -d, --model-dir DIR     Model directory (default: $DEFAULT_MODEL_DIR)
    -s, --skip-download     Skip model download step
    -b, --skip-build        Skip Docker build step
    -t, --hf-token TOKEN    Hugging Face token for private models
    --fix-prereqs          Auto-fix common prerequisite issues
    --skip-gpu-check       Skip GPU/CUDA validation

Examples:
    $0                                          # Full setup with default model
    $0 --fix-prereqs                           # Fix common issues first
    $0 -m microsoft/DialoGPT-large             # Use different model
    $0 -s                                      # Skip download, just build and run

Field-tested workflow:
    1. Check and fix GPU/Docker prerequisites
    2. Download model (if needed)
    3. Build container with proper caching
    4. Launch with health checks
EOF
}

# Function to check NVIDIA drivers and CUDA
check_nvidia_setup() {
    log "🔍 Checking NVIDIA drivers and CUDA..."
    
    # Check nvidia-smi
    if ! command -v nvidia-smi &> /dev/null; then
        error "nvidia-smi not found. NVIDIA drivers not installed."
        return 1
    fi
    
    # Check NVML initialization
    if ! nvidia-smi > /dev/null 2>&1; then
        error "nvidia-smi failed to initialize NVML"
        error "This usually means driver/NVML version mismatch"
        error "Fix: Purge all NVIDIA packages and reinstall matching versions"
        info "sudo apt-get purge nvidia-* libnvidia-*"
        info "sudo ubuntu-drivers autoinstall  # or install specific version"
        return 1
    fi
    
    # Show GPU information
    local gpu_count=$(nvidia-smi --list-gpus | wc -l)
    info "✅ NVIDIA drivers OK - Found $gpu_count GPU(s)"
    nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader,nounits | while IFS=, read -r index name memory; do
        info "  GPU $index: $name ($memory MB)"
    done
    
    # Check CUDA availability (optional for Docker-based TGI)
    if command -v nvcc &> /dev/null; then
        local cuda_version=$(nvcc --version | grep "release" | sed 's/.*release //' | sed 's/,.*//')
        info "✅ CUDA toolkit found: $cuda_version"
    else
        warn "CUDA toolkit not found (OK for Docker-based TGI)"
    fi
    
    return 0
}

# Function to check and fix Docker installation
check_docker_setup() {
    log "🔍 Checking Docker setup..."
    
    # Check Docker command
    if ! command -v docker &> /dev/null; then
        error "Docker not found. Installing Docker CE..."
        install_docker_ce
        return $?
    fi
    
    # Check Docker service
    if ! systemctl is-active --quiet docker; then
        error "Docker service not running"
        if systemctl list-unit-files docker.service | grep -q masked; then
            error "Docker service is masked"
            info "Fixing: sudo systemctl unmask docker.service docker.socket"
            sudo systemctl unmask docker.service docker.socket
        fi
        
        info "Starting Docker service..."
        sudo systemctl enable --now docker
        sleep 3
    fi
    
    # Check Docker permissions
    if ! docker info > /dev/null 2>&1; then
        if [[ $? -eq 1 ]] && docker info 2>&1 | grep -q "permission denied"; then
            error "Permission denied accessing Docker socket"
            info "Adding user to docker group..."
            sudo usermod -aG docker $USER
            warn "Please logout and login again for docker group changes to take effect"
            warn "Or run: newgrp docker"
            return 1
        fi
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose not found"
        info "Installing Docker Compose..."
        install_docker_compose
        return $?
    fi
    
    info "✅ Docker setup OK"
    return 0
}

# Function to install Docker CE
install_docker_ce() {
    log "📦 Installing Docker CE..."
    
    # Remove old versions
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Setup repository
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Add repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Start and enable service
    sudo systemctl enable --now docker
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    info "✅ Docker CE installed successfully"
    return 0
}

# Function to install Docker Compose
install_docker_compose() {
    if docker compose version &> /dev/null; then
        info "✅ Docker Compose (plugin) already available"
        return 0
    fi
    
    # Install standalone docker-compose
    local compose_version=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')
    sudo curl -L "https://github.com/docker/compose/releases/download/$compose_version/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    info "✅ Docker Compose installed successfully"
    return 0
}

# Function to check and install NVIDIA Container Toolkit
check_nvidia_container_toolkit() {
    log "🔍 Checking NVIDIA Container Toolkit..."
    
    # Check if toolkit is installed
    if ! command -v nvidia-ctk &> /dev/null; then
        error "NVIDIA Container Toolkit not found. Installing..."
        install_nvidia_container_toolkit
        return $?
    fi
    
    # Check Docker runtime configuration
    if ! docker info --format '{{json .Runtimes}}' 2>/dev/null | grep -q nvidia; then
        error "NVIDIA runtime not configured in Docker"
        info "Configuring NVIDIA runtime..."
        sudo nvidia-ctk runtime configure --runtime=docker
        sudo systemctl restart docker
        sleep 5
    fi
    
    # Test GPU access in container
    if ! docker run --rm --gpus all nvidia/cuda:12.2-base-ubuntu22.04 nvidia-smi > /dev/null 2>&1; then
        error "GPU not accessible in containers"
        error "Check NVIDIA Container Toolkit configuration"
        return 1
    fi
    
    info "✅ NVIDIA Container Toolkit OK"
    return 0
}

# Function to install NVIDIA Container Toolkit
install_nvidia_container_toolkit() {
    log "📦 Installing NVIDIA Container Toolkit..."
    
    # Add GPG key
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit.gpg
    
    # Add repository
    local ubuntu_version=$(lsb_release -cs)
    curl -fsSL https://nvidia.github.io/libnvidia-container/$ubuntu_version/libnvidia-container.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit.gpg] https://#' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    # Install toolkit
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    
    # Configure Docker runtime
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    
    info "✅ NVIDIA Container Toolkit installed successfully"
    return 0
}

# Function to check Python environment
check_python_setup() {
    log "🔍 Checking Python environment..."
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        error "Python 3 not found"
        return 1
    fi
    
    # Check python3-venv
    if ! python3 -m venv --help > /dev/null 2>&1; then
        error "python3-venv not available"
        info "Installing python3-venv..."
        local python_version=$(python3 --version | sed 's/Python //' | sed 's/\.[0-9]*$//')
        sudo apt-get update
        sudo apt-get install -y python3-venv python3-pip
    fi
    
    info "✅ Python environment OK"
    return 0
}

# Function to check disk space
check_disk_space() {
    log "🔍 Checking disk space..."
    
    local available_space=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$available_space" -lt "$REQUIRED_DISK_SPACE_GB" ]; then
        error "Insufficient disk space: ${available_space}GB available, ${REQUIRED_DISK_SPACE_GB}GB required"
        error "Please free up space or use a different location"
        return 1
    fi
    
    info "✅ Disk space OK: ${available_space}GB available"
    return 0
}

# Function to run comprehensive prerequisites check
check_prerequisites() {
    log "🔍 Running comprehensive prerequisites check..."
    
    local failed_checks=0
    
    # Check Python first (needed for model download)
    check_python_setup || ((failed_checks++))
    
    # Check disk space
    check_disk_space || ((failed_checks++))
    
    # Check NVIDIA setup (if not skipping GPU check)
    if [ "$SKIP_GPU_CHECK" != "true" ]; then
        check_nvidia_setup || ((failed_checks++))
        check_nvidia_container_toolkit || ((failed_checks++))
    fi
    
    # Check Docker setup
    check_docker_setup || ((failed_checks++))
    
    if [ $failed_checks -gt 0 ]; then
        error "❌ $failed_checks prerequisite check(s) failed"
        return 1
    fi
    
    info "✅ All prerequisites check passed"
    return 0
}

# Function to download model
download_model() {
    local model_id="$1"
    local model_dir="$2"
    local hf_token="$3"
    
    log "📥 Downloading model: $model_id"
    log "📁 Target directory: $model_dir"
    
    # Download using the standalone script
    local download_cmd="python3 download_model.py --model-id '$model_id' --output-dir '$model_dir'"
    if [ -n "$hf_token" ]; then
        download_cmd="$download_cmd --hf-token '$hf_token'"
    fi
    
    info "Running: $download_cmd"
    if eval $download_cmd; then
        info "✅ Model download completed"
        return 0
    else
        error "❌ Model download failed"
        return 1
    fi
}

# Function to build container
build_container() {
    log "🔨 Building TGI container..."
    
    # Create .dockerignore to avoid large build context
    cat > .dockerignore << EOF
models/
*.log
.git/
__pycache__/
*.pyc
.venv/
.env
EOF
    
    # Build with proper cache handling
    if docker compose build --pull; then
        info "✅ Container build completed"
        return 0
    else
        error "❌ Container build failed"
        return 1
    fi
}

# Function to start TGI with health checks
start_tgi() {
    local model_dir="$1"
    
    log "🚀 Starting TGI service..."
    
    # Export model path for docker-compose
    export MODEL_HOST_PATH="$(realpath "$model_dir")"
    info "Model path: $MODEL_HOST_PATH"
    
    # Start the service
    if docker compose up -d; then
        info "✅ TGI service started"
        
        # Wait for service to be ready with better error handling
        log "⏳ Waiting for TGI to be ready..."
        local max_attempts=60  # 10 minutes
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
                break
            fi
            
            # Check if container is still running
            if ! docker compose ps --services --filter "status=running" | grep -q tgi; then
                error "❌ TGI container stopped unexpectedly"
                error "Check logs with: docker compose logs tgi"
                return 1
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                error "❌ TGI failed to start within timeout"
                error "Check logs with: docker compose logs tgi"
                return 1
            fi
            
            echo -n "."
            sleep 10
            ((attempt++))
        done
        
        echo ""
        log "🎉 TGI is ready and healthy!"
        
        # Show service information
        info "🔗 Service Information:"
        info "  API endpoint: http://localhost:8080"
        info "  Health check: curl http://localhost:8080/health"
        info "  Logs: docker compose logs -f tgi"
        
        # Test basic functionality
        log "🧪 Testing basic functionality..."
        local test_response=$(curl -s -X POST http://localhost:8080/generate \
            -H "Content-Type: application/json" \
            -d '{"inputs":"Hello!","parameters":{"max_new_tokens":16}}' | jq -r .generated_text 2>/dev/null)
        
        if [ -n "$test_response" ]; then
            info "✅ Basic test passed: $test_response"
        else
            warn "⚠️  Basic test failed, but service is running"
        fi
        
        return 0
    else
        error "❌ Failed to start TGI service"
        return 1
    fi
}

# Function to fix common prerequisites issues
fix_prerequisites() {
    log "🔧 Attempting to fix common prerequisite issues..."
    
    # Update package lists
    sudo apt-get update
    
    # Install basic tools
    sudo apt-get install -y curl wget gnupg lsb-release software-properties-common
    
    # Try to install Docker CE
    if ! command -v docker &> /dev/null; then
        install_docker_ce
    fi
    
    # Try to install NVIDIA Container Toolkit
    if [ "$SKIP_GPU_CHECK" != "true" ] && ! command -v nvidia-ctk &> /dev/null; then
        install_nvidia_container_toolkit
    fi
    
    # Install Python venv
    if ! python3 -m venv --help > /dev/null 2>&1; then
        sudo apt-get install -y python3-venv python3-pip
    fi
    
    info "✅ Common fixes applied"
}

# Main function
main() {
    local model_id="$DEFAULT_MODEL"
    local model_dir="$DEFAULT_MODEL_DIR"
    local hf_token=""
    local skip_download=false
    local skip_build=false
    local fix_prereqs=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -m|--model-id)
                model_id="$2"
                shift 2
                ;;
            -d|--model-dir)
                model_dir="$2"
                shift 2
                ;;
            -t|--hf-token)
                hf_token="$2"
                shift 2
                ;;
            -s|--skip-download)
                skip_download=true
                shift
                ;;
            -b|--skip-build)
                skip_build=true
                shift
                ;;
            --fix-prereqs)
                fix_prereqs=true
                shift
                ;;
            --skip-gpu-check)
                SKIP_GPU_CHECK=true
                shift
                ;;
            *)
                error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    log "🚀 Starting TGI installation process..."
    log "Model ID: $model_id"
    log "Model Directory: $model_dir"
    
    # Apply fixes if requested
    if [ "$fix_prereqs" = true ]; then
        fix_prerequisites
    fi
    
    # Step 1: Check prerequisites
    if ! check_prerequisites; then
        error "❌ Prerequisites check failed"
        info "💡 Try running with --fix-prereqs flag to auto-fix common issues"
        exit 1
    fi
    
    # Step 2: Download model (optional)
    if [ "$skip_download" = false ]; then
        if ! download_model "$model_id" "$model_dir" "$hf_token"; then
            exit 1
        fi
    else
        warn "⏭️ Skipping model download"
        if [ ! -d "$model_dir" ]; then
            error "Model directory $model_dir does not exist"
            exit 1
        fi
    fi
    
    # Step 3: Build container (optional)
    if [ "$skip_build" = false ]; then
        if ! build_container; then
            exit 1
        fi
    else
        warn "⏭️ Skipping container build"
    fi
    
    # Step 4: Start TGI
    if ! start_tgi "$model_dir"; then
        exit 1
    fi
    
    # Final success message
    log "🎉 TGI installation completed successfully!"
    log ""
    log "📚 Common management commands:"
    log "  • View logs: docker compose logs -f tgi"
    log "  • Stop service: docker compose down"
    log "  • Restart: docker compose restart tgi"
    log "  • Check status: docker compose ps"
    log "  • Resource usage: docker stats tgi-gemma3"
    log ""
    log "🧪 Test API:"
    log "  curl -X POST http://localhost:8080/generate \\"
    log "    -H 'Content-Type: application/json' \\"
    log "    -d '{\"inputs\":\"Hello!\",\"parameters\":{\"max_new_tokens\":16}}'"
}

# Run main function with all arguments
main "$@"
