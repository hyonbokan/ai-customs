Below is a complete, end-to-end recipe for building your own Docker image that bundles Text-Generation-Inference (TGI) plus your local Gemma 3 model—so you never have to rebuild from source or mount volumes at runtime. This image will:

Install the NVIDIA Container Toolkit runtime for GPU support

Install TGI via the official Hugging Face Docker image as a base

Copy in your Gemma 3 model files

Expose the proper ports and set the entrypoint to text-generation-launcher

Support multi-GPU sharding via build-time defaults or runtime flags

1. Prerequisites
A machine with Docker (with NVIDIA GPU support) already installed and working.

Your model directory at ~/models/gemma-3-27b-it containing config.json, weights, tokenizer files, etc.

Basic familiarity with Dockerfiles and docker build / docker run.

2. Create the Dockerfile
In an empty folder (e.g. tgi-gemma3-docker), create a file named Dockerfile with the following contents:

dockerfile
# 1. Base on Hugging Face’s official TGI image (includes FlashAttention etc.)
FROM ghcr.io/huggingface/text-generation-inference:latest

# 2. Metadata
LABEL maintainer="dnlab <dnlab@your.org>"
LABEL description="TGI server with Gemma 3 27B, multi-GPU ready"

# 3. Create a directory for the model
RUN mkdir -p /opt/models/gemma-3-27b-it

# 4. Copy your local model into the image
#    Adjust the source path if your build context differs
COPY --chown=1000:1000 models/gemma-3-27b-it /opt/models/gemma-3-27b-it

# 5. (Optional) Install any extra Python packages you need
# RUN pip install some-extra-lib

# 6. Expose TGI’s default port
EXPOSE 8080

# 7. Set environment variables for optimal GPU usage
ENV RUST_LOG="info" \
    TGI_LOG_LEVEL="info"

# 8. Entrypoint: launch TGI pointing at your baked-in model
ENTRYPOINT ["text-generation-launcher"]
CMD [
  "--model-id", "/opt/models/gemma-3-27b-it",
  "--trust-remote-code",
  "--host", "0.0.0.0",
  "--port", "8080",
  "--num-shard", "2"           # default to 2 shards; override at runtime if needed
]
Notes:

We use the official TGI image as base so all Rust/Python/CUDA kernels are prebuilt.

Adjust --num-shard to your target GPU count or remove it to require runtime flags.

COPY models/gemma-3-27b-it assumes you place your models/ folder next to this Dockerfile.

3. Build the Docker image
From within the tgi-gemma3-docker directory, run:

bash
Copy
Edit
docker build -t tgi-gemma3:latest .
-t tgi-gemma3:latest gives your new image a friendly name.

This will copy in ~100 GB of model weights—plan for a few minutes of build time.

4. Push to a Registry (optional)
If you want to distribute this image to colleagues or a k8s cluster:

bash
Copy
Edit
# Tag for your registry
docker tag tgi-gemma3:latest myregistry.example.com/dnlab/tgi-gemma3:latest

# Push
docker push myregistry.example.com/dnlab/tgi-gemma3:latest
5. Run your container
Now launch your server with GPU support:

bash
Copy
Edit
docker run --gpus all \
  -d \
  --name tgi-gemma3 \
  -p 8080:8080 \
  tgi-gemma3:latest
--gpus all enables all NVIDIA GPUs inside the container.

-d detaches so it runs in the background.

You can override shard count at runtime, e.g.:

bash
Copy
Edit
docker exec tgi-gemma3 text-generation-launcher \
  --model-id /opt/models/gemma-3-27b-it \
  --trust-remote-code \
  --host 0.0.0.0 \
  --port 8080 \
  --num-shard 4
or simply rebuild with a different default.

6. Verify it’s working
bash
Copy
Edit
docker logs -f tgi-gemma3 | grep "Serving on"
# Then test with curl:
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"inputs":"Hello, Gemma 3!","parameters":{"max_new_tokens":20}}'
You should see a valid JSON response with your model’s output.

7. Tuning & Maintenance
Model updates: Rebuild the image after replacing weights or config in models/gemma-3-27b-it.

Extra deps: If you need Python libs (e.g. accelerate, peft), add a RUN pip install … step before the ENTRYPOINT.

Logging: Mount a host volume to capture logs outside the container:

bash
Copy
Edit
docker run … -v ~/tgi-logs:/var/log/tgi tgi-gemma3:latest
Security: Drop privileges by adding USER 1000 under your ENTRYPOINT if you baked in a non-root user.