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


sudo docker run --gpus all -v ~/models/gpt-oss-20b:/models/gpt-oss-20b -p 8080:80 ghcr.io/huggingface/text-generation-inference:latest --model-id /models/gpt-oss-20b --trust-remote-code --num-shard 2


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
2025-07-04T12:35:04.335552Z  INFO text_generation_launcher: Disabling prefix caching because of VLM model
2025-07-04T12:35:04.335574Z  INFO text_generation_launcher: Using attention flashinfer - Prefix caching 0
2025-07-04T12:35:04.335583Z  INFO text_generation_launcher: Sharding model on 2 processes
2025-07-04T12:35:04.371888Z  WARN text_generation_launcher: Unkown compute for card nvidia-rtx-a6000
2025-07-04T12:35:04.406179Z  INFO text_generation_launcher: Default `max_batch_prefill_tokens` to 8000
2025-07-04T12:35:04.406208Z  INFO text_generation_launcher: Using default cuda graphs [1, 2, 4, 8, 16, 32]
2025-07-04T12:35:04.406219Z  WARN text_generation_launcher: `trust_remote_code` is set. Trusting that model `/models/gemma-3-27b-it` do not contain malicious code.
2025-07-04T12:35:04.406496Z  INFO download: text_generation_launcher: Starting check and download process for /models/gemma-3-27b-it
2025-07-04T12:35:08.906826Z  INFO text_generation_launcher: Files are already present on the host. Skipping download.
2025-07-04T12:35:09.843082Z  INFO download: text_generation_launcher: Successfully downloaded weights for /models/gemma-3-27b-it
2025-07-04T12:35:09.843564Z  INFO shard-manager: text_generation_launcher: Starting shard rank=0
2025-07-04T12:35:09.843565Z  INFO shard-manager: text_generation_launcher: Starting shard rank=1
2025-07-04T12:35:14.715080Z  INFO text_generation_launcher: Using prefix caching = False
2025-07-04T12:35:14.715114Z  INFO text_generation_launcher: Using Attention = flashinfer
2025-07-04T12:35:19.889835Z  INFO shard-manager: text_generation_launcher: Waiting for shard to be ready... rank=1
2025-07-04T12:35:19.898784Z  INFO shard-manager: text_generation_launcher: Waiting for shard to be ready... rank=0
2025-07-04T12:35:29.905235Z  INFO shard-manager: text_generation_launcher: Waiting for shard to be ready... rank=1
2025-07-04T12:35:29.912327Z  INFO shard-manager: text_generation_launcher: Waiting for shard to be ready... rank=0
2025-07-04T12:35:39.919849Z  INFO shard-manager: text_generation_launcher: Waiting for shard to be ready... rank=1
2025-07-04T12:35:39.925799Z  INFO shard-manager: text_generation_launcher: Waiting for shard to be ready... rank=0
2025-07-04T12:35:49.935040Z  INFO shard-manager: text_generation_launcher: Waiting for shard to be ready... rank=1
2025-07-04T12:35:49.938792Z  INFO shard-manager: text_generation_launcher: Waiting for shard to be ready... rank=0
2025-07-04T12:35:57.436893Z  INFO text_generation_launcher: Using prefill chunking = False
2025-07-04T12:35:58.091901Z  INFO text_generation_launcher: Server started at unix:///tmp/text-generation-server-0
2025-07-04T12:35:58.150338Z  INFO shard-manager: text_generation_launcher: Shard ready in 48.277857716s rank=0
2025-07-04T12:35:58.225726Z  INFO text_generation_launcher: Server started at unix:///tmp/text-generation-server-1
2025-07-04T12:35:58.247141Z  INFO shard-manager: text_generation_launcher: Shard ready in 48.385111561s rank=1
2025-07-04T12:35:58.312507Z  INFO text_generation_launcher: Starting Webserver
2025-07-04T12:35:58.387723Z  INFO text_generation_router_v3: backends/v3/src/lib.rs:125: Warming up model
2025-07-04T12:35:58.711357Z  INFO text_generation_launcher: Using optimized Triton indexing kernels.
2025-07-04T12:36:00.922473Z  INFO text_generation_launcher: image_id 0 start_idx 0 end_idx 258, length 258
2025-07-04T12:36:00.926789Z  INFO text_generation_launcher: image_id 0 start_idx 0 end_idx 258, length 258
2025-07-04T12:36:06.251692Z  INFO text_generation_launcher: KV-cache blocks: 52719, size: 1
2025-07-04T12:36:06.364197Z  INFO text_generation_launcher: Cuda Graphs are enabled for sizes [32, 16, 8, 4, 2, 1]
2025-07-04T12:36:09.356551Z  INFO text_generation_router_v3: backends/v3/src/lib.rs:137: Setting max batch total tokens to 52125
2025-07-04T12:36:09.356591Z  INFO text_generation_router_v3: backends/v3/src/lib.rs:166: Using backend V3
2025-07-04T12:36:09.356600Z  INFO text_generation_router: backends/v3/src/main.rs:165: Maximum input tokens defaulted to 7999
2025-07-04T12:36:09.356606Z  INFO text_generation_router: backends/v3/src/main.rs:171: Maximum total tokens defaulted to 8000
2025-07-04T12:36:09.356768Z  WARN text_generation_router::server: router/src/server.rs:1673: Tokenizer_config None - Some("/models/gemma-3-27b-it/tokenizer_config.json")
2025-07-04T12:36:09.362256Z  INFO text_generation_router::server: router/src/server.rs:1686: Using chat template from chat_template.json
2025-07-04T12:36:15.150564Z  INFO text_generation_router::server: router/src/server.rs:1741: Using config Some(Gemma3(Gemma3 { vision_config: Gemma3VisionConfig { image_size: 896, patch_size: 14 } }))
2025-07-04T12:36:15.150625Z  WARN text_generation_router::server: router/src/server.rs:1801: no pipeline tag found for model /models/gemma-3-27b-it
2025-07-04T12:36:15.150636Z  WARN text_generation_router::server: router/src/server.rs:1906: Invalid hostname, defaulting to 0.0.0.0
2025-07-04T12:36:15.367126Z  INFO text_generation_router::server: router/src/server.rs:2298: Connected