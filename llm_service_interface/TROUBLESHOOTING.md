# TGI Troubleshooting Guide - Field-Tested Solutions

This guide addresses the **most common issues** encountered when deploying TGI, based on real-world experience. Issues are ordered by frequency of occurrence.

## 🚨 Quick Diagnostic

Run this command to quickly identify common issues:

```bash
# Run automated diagnostics
./install.sh --fix-prereqs --skip-download --skip-build

# Manual checks
docker run --rm --gpus all nvidia/cuda:12.2-base-ubuntu22.04 nvidia-smi
docker compose config
curl -f http://localhost:8080/health
```

---

## 🔥 Critical Issues (Order of Frequency)

### 1. GPU & Driver Issues

#### **Issue**: `nvidia-smi: Failed to initialize NVML`
**Symptoms**: GPU not detected, driver errors
**Cause**: Driver/NVML version mismatch

**Solution**:
```bash
# Check current driver
nvidia-smi

# If failed, purge and reinstall
sudo apt-get purge nvidia-* libnvidia-*
sudo apt-get autoremove
sudo ubuntu-drivers autoinstall
# OR install specific version:
# sudo apt-get install nvidia-driver-535

# Reboot and verify
sudo reboot
nvidia-smi
```

#### **Issue**: `CUDA_HOME not set` or Flash-Attention build fails
**Symptoms**: Build errors, missing CUDA toolkit
**Cause**: Missing CUDA development tools

**Solution**:
```bash
# Option 1: Use pre-built Docker image (RECOMMENDED)
# No need to install CUDA toolkit

# Option 2: Install CUDA toolkit if building from source
sudo apt-get install cuda-toolkit-12-1
export CUDA_HOME=/usr/local/cuda-12.1
export PATH=$PATH:/usr/local/cuda-12.1/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda-12.1/lib64
```

### 2. Python Environment Issues

#### **Issue**: `ensurepip is not available`
**Symptoms**: Virtual environment creation fails
**Cause**: Missing python3-venv package

**Solution**:
```bash
# Install python3-venv
sudo apt-get update
sudo apt-get install python3.10-venv python3-pip

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
```

#### **Issue**: VS Code uses wrong Python interpreter
**Symptoms**: Import errors, wrong packages
**Cause**: VS Code pointing to system Python

**Solution**:
```bash
# In VS Code
# Ctrl+Shift+P → Python: Select Interpreter
# Choose: .venv/bin/python

# Save to workspace
echo '{"python.defaultInterpreterPath": "./.venv/bin/python"}' > .vscode/settings.json
```

### 3. Docker Engine Problems

#### **Issue**: `docker-ce has no installation candidate`
**Symptoms**: Docker installation fails
**Cause**: Missing repository or GPG key

**Solution**:
```bash
# Clean setup
sudo apt-get remove docker docker-engine docker.io containerd runc

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

#### **Issue**: `Unit docker.service is masked`
**Symptoms**: Docker service won't start
**Cause**: Previous Docker installation conflicts

**Solution**:
```bash
# Unmask and restart
sudo systemctl unmask docker.service docker.socket
sudo systemctl enable docker.service
sudo systemctl start docker.service

# Check status
sudo systemctl status docker
```

#### **Issue**: `Permission denied` on `/var/run/docker.sock`
**Symptoms**: Docker commands fail for non-root user
**Cause**: User not in docker group

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply changes (choose one):
# Option 1: Logout and login again
# Option 2: Use newgrp
newgrp docker

# Verify
docker ps
```

### 4. NVIDIA Container Toolkit Issues

#### **Issue**: GPG key errors or 404 on repository
**Symptoms**: Repository not found, key verification fails
**Cause**: Wrong repository URL or missing GPG key

**Solution**:
```bash
# Correct installation
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit.gpg

# Add repository (adjust for your Ubuntu version)
curl -fsSL https://nvidia.github.io/libnvidia-container/ubuntu22.04/libnvidia-container.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit.gpg] https://#' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install
sudo apt-get update
sudo apt-get install nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

#### **Issue**: `could not select device driver "" with capabilities: [[gpu]]`
**Symptoms**: Container can't access GPU
**Cause**: Runtime not configured or Docker not restarted

**Solution**:
```bash
# Configure runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.2-base-ubuntu22.04 nvidia-smi
```

### 5. TGI Runtime Issues

#### **Issue**: Single-GPU OOM (Out of Memory)
**Symptoms**: GPU memory exceeded, CUDA errors
**Cause**: Large model on single GPU

**Solution**:
```bash
# Use multiple GPUs
export TGI_NUM_SHARD=2  # or more
docker compose up -d

# OR reduce batch size
export TGI_MAX_BATCH_PREFILL_TOKENS=2048
export TGI_MAX_BATCH_TOTAL_TOKENS=4096
export TGI_MAX_CONCURRENT_REQUESTS=64
```

#### **Issue**: Structured output errors
**Symptoms**: API calls fail with schema errors
**Cause**: Using wrong client or parameters

**Solution**:
```bash
# Use correct client
# Wrong: text-generation.InferenceAPIClient()
# Right: huggingface_hub.InferenceClient()

# Or specify model parameter
client = InferenceAPIClient(model="tgi")
```

### 6. Model Issues

#### **Issue**: Model download incomplete or corrupted
**Symptoms**: Missing config.json, empty model files
**Cause**: Interrupted download, insufficient disk space

**Solution**:
```bash
# Check disk space
df -h

# Re-download model
rm -rf models/
python3 download_model.py --model-id google/gemma-2-27b-it

# Verify model integrity
ls -la models/gemma-2-27b-it/
cat models/gemma-2-27b-it/config.json
```

#### **Issue**: Model not found in container
**Symptoms**: "No config.json found" errors
**Cause**: Incorrect volume mount or permissions

**Solution**:
```bash
# Check volume mount
export MODEL_HOST_PATH=$(realpath ./models)
echo "Model path: $MODEL_HOST_PATH"

# Check permissions
sudo chown -R 1000:1000 models/
ls -la models/

# Verify mount inside container
docker exec tgi-gemma3 ls -la /opt/models/
```

---

## 🔧 Performance Optimization

### GPU Memory Optimization

```bash
# For 24GB GPUs
export TGI_MAX_CONCURRENT_REQUESTS=64
export TGI_MAX_TOTAL_TOKENS=4096
export TGI_MAX_BATCH_PREFILL_TOKENS=2048

# For 48GB+ GPUs
export TGI_MAX_CONCURRENT_REQUESTS=256
export TGI_MAX_TOTAL_TOKENS=8192
export TGI_MAX_BATCH_PREFILL_TOKENS=4096
```

### Multi-GPU Setup

```bash
# Auto-detect GPUs
export TGI_NUM_SHARD=auto

# Manual configuration
export TGI_NUM_SHARD=2
export CUDA_VISIBLE_DEVICES=0,1

# Verify GPU usage
nvidia-smi -l 1
```

### Latency Optimization

```bash
# Reduce waiting time
export TGI_WAITING_SERVED_RATIO=0.8

# Smaller batch sizes
export TGI_MAX_BATCH_PREFILL_TOKENS=1024
export TGI_MAX_BATCH_TOTAL_TOKENS=2048
```

---

## 📊 Monitoring & Debugging

### Real-time Monitoring

```bash
# Container resources
docker stats tgi-gemma3

# GPU utilization
nvidia-smi -l 1

# Service logs
docker compose logs -f tgi

# System resources
htop
```

### Health Checks

```bash
# Service health
curl -f http://localhost:8080/health

# Basic functionality
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"inputs":"Hello!","parameters":{"max_new_tokens":16}}'

# Container status
docker compose ps
```

### Log Analysis

```bash
# View logs
docker compose logs tgi | tail -100

# Filter errors
docker compose logs tgi | grep -i error

# Check startup sequence
docker compose logs tgi | grep -E "(Starting|Ready|Error)"
```

---

## 🚨 Emergency Procedures

### Complete Reset

```bash
# Stop everything
docker compose down

# Remove containers and images
docker system prune -a

# Reset configuration
rm -rf .venv/
rm -rf models/

# Start fresh
./install.sh --fix-prereqs
```

### Service Recovery

```bash
# Restart service
docker compose restart tgi

# Rebuild container
docker compose build --no-cache
docker compose up -d

# Check hardware
nvidia-smi
docker info
```

### Data Recovery

```bash
# Backup important data
cp -r models/ models_backup/
docker compose logs tgi > tgi_logs_backup.txt

# Restore from backup
rsync -av models_backup/ models/
```

---

## 🆘 Getting Help

### Collect Debug Information

```bash
# System info
echo "=== System Information ===" > debug_info.txt
uname -a >> debug_info.txt
lsb_release -a >> debug_info.txt

# GPU info
echo "=== GPU Information ===" >> debug_info.txt
nvidia-smi >> debug_info.txt

# Docker info
echo "=== Docker Information ===" >> debug_info.txt
docker version >> debug_info.txt
docker info >> debug_info.txt

# Service logs
echo "=== Service Logs ===" >> debug_info.txt
docker compose logs --tail=100 tgi >> debug_info.txt
```

### Common Commands Reference

```bash
# Start service
docker compose up -d

# View logs
docker compose logs -f tgi

# Stop service
docker compose down

# Restart service
docker compose restart tgi

# Check status
docker compose ps

# Update container
docker compose pull
docker compose up -d

# Shell access
docker exec -it tgi-gemma3 /bin/bash

# Resource monitoring
docker stats tgi-gemma3
```

---

## 📋 Validation Checklist

Before reporting issues, verify:

- [ ] NVIDIA drivers installed and working (`nvidia-smi`)
- [ ] Docker service running (`sudo systemctl status docker`)
- [ ] Docker group membership (`groups | grep docker`)
- [ ] NVIDIA Container Toolkit installed (`nvidia-ctk --version`)
- [ ] GPU accessible in containers (`docker run --rm --gpus all nvidia/cuda:12.2-base-ubuntu22.04 nvidia-smi`)
- [ ] Model downloaded and complete (`ls -la models/*/config.json`)
- [ ] Sufficient disk space (`df -h`)
- [ ] Correct permissions (`ls -la models/`)
- [ ] Service healthy (`curl -f http://localhost:8080/health`)

---

## 🔗 Additional Resources

- [TGI Documentation](https://github.com/huggingface/text-generation-inference)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Ubuntu GPU Drivers](https://ubuntu.com/server/docs/nvidia-drivers-installation) 