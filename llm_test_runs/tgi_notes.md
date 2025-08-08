1. Docker launch options
sudo docker run --gpus all
Grants the container access to all available NVIDIA GPUs on the host. Without this, the container cannot see or use your GPUs for inference. 
stackoverflow.com
docs.nvidia.com

-v ~/models/gemma-3-27b-it:/models/gemma-3-27b-it
Bind-mounts your local ~/models/gemma-3-27b-it directory into the exact same path inside the container. This way TGI sees the model files you already downloaded, instead of pulling from the hub. 
reddit.com
forums.docker.com

-p 8080:80
Maps port 80 inside the container (where TGI listens by default) to port 8080 on your host machine. You’ll then call TGI at http://localhost:8080. 
stackoverflow.com
dev-diaries.com

2. Which image to run
ghcr.io/huggingface/text-generation-inference:latest
Specifies the official TGI Docker image (latest tag) hosted on GitHub Container Registry. This image bundles the Rust/Python server capable of high-performance LLM inference. 
github.com
huggingface.co

3. TGI-specific launcher flags
--model-id /models/gemma-3-27b-it
Tells TGI which model to load. You can point at any Hugging Face hub ID or a local directory (as here) containing config.json and model weights. 
huggingface.co

--trust-remote-code
Allows execution of custom model‐definition code shipped alongside the weights. Required for models that include special architecture or tokenizer logic. 
huggingface.co

--num-shard 2
Activates tensor parallelism, splitting the model into 2 shards and loading them across GPUs. Use this when a single GPU can’t hold the entire model or you want faster throughput.

Command to run the Gemma 3 27B model with TGI in Docker:

sudo docker run --gpus all -v ~/models/gemma-3-27b-it:/models/gemma-3-27b-it -p 8080:80 ghcr.io/huggingface/text-generation-inference:latest --model-id /models/gemma-3-27b-it --trust-remote-code --num-shard 2


sudo docker run --gpus all -v ~/models/gpt-oss-20b:/models/gpt-oss-20b -p 8080:80 ghcr.io/huggingface/text-generation-inference:latest --model-id /models/gpt-oss-20b --trust-remote-code--num-shard 2


2025-07-04T12:35:02.586768Z  INFO text_generation_launcher: Args {
    model_id: "/models/gemma-3-27b-it",
    revision: None,
    validation_workers: 2,
    sharded: None,
    num_shard: Some(
        2,
    ),
    quantize: None,
    speculate: None,
    dtype: None,
    kv_cache_dtype: None,
    trust_remote_code: true,
    max_concurrent_requests: 128,
    max_best_of: 2,
    max_stop_sequences: 4,
    max_top_n_tokens: 5,
    max_input_tokens: None,
    max_input_length: None,
    max_total_tokens: None,
    waiting_served_ratio: 0.3,
    max_batch_prefill_tokens: None,
    max_batch_total_tokens: None,
    max_waiting_tokens: 20,
    max_batch_size: None,
    cuda_graphs: None,
    hostname: "dd620800ae90",
    port: 80,
    prometheus_port: 9000,
    shard_uds_path: "/tmp/text-generation-server",
    master_addr: "localhost",
    master_port: 29500,
    huggingface_hub_cache: None,
    weights_cache_override: None,
    disable_custom_kernels: false,
    cuda_memory_fraction: 1.0,
    rope_scaling: None,
    rope_factor: None,
    json_output: false,
    otlp_endpoint: None,
    otlp_service_name: "text-generation-inference.router",
    cors_allow_origin: [],
    api_key: None,
    watermark_gamma: None,
    watermark_delta: None,
    ngrok: false,
    ngrok_authtoken: None,
    ngrok_edge: None,
    tokenizer_config_path: None,
    disable_grammar_support: false,
    env: false,
    max_client_batch_size: 4,
    lora_adapters: None,
    usage_stats: On,
    payload_limit: 2000000,
    enable_prefill_logprobs: false,
    graceful_termination_timeout: 90,
}