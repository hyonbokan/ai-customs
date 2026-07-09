# AI Customs Backend

This is the backend for the AI Customs project, a FastAPI application designed to analyze customs declarations using large language models.

## Running with Docker

This is the recommended way to run the backend, as it encapsulates all dependencies and ensures a consistent environment.

### Prerequisites

- Docker installed on your system.
- Your user must have permissions to run Docker commands (or you must use `sudo`).

### 1. Build the Docker Image

From the project's root directory (`ai-customs/`), run the following command to build the Docker image. The `-f` flag points to the `Dockerfile` inside the `backend` directory, and the `.` at the end specifies the build context (the entire project root).

```bash
docker build -t customs-ai-backend -f backend/Dockerfile .
```

### 2. Run the Docker Container

To run the container and expose the API on your local machine at port 8000:

```bash
docker run -p 8000:8000 --name customs-ai-container customs-ai-backend
```

- `-p 8000:8000`: Maps port 8000 on your host machine to port 8000 inside the container.
- `--name customs-ai-container`: Assigns a convenient name to your running container.

### 3. Connecting to the LLM (vLLM / TGI) Service

The model server runs separately. vLLM is the primary engine; to serve
Gemma-3-27B with vLLM on two GPUs:

```bash
sudo docker run --gpus all \
  -v ~/models/gemma-3-27b-it:/models/gemma-3-27b-it \
  -p 8080:80 --shm-size 2g \
  vllm/vllm-openai:latest \
  --model /models/gemma-3-27b-it --served-model-name gemma-3-27b-it \
  --dtype auto --port 80 --tensor-parallel-size 2
```

TGI is also supported as an alternative — see
[`../llm_service_manual/`](../llm_service_manual/).

The backend reaches the model over the `LLM_BASE_URL` environment variable.
Set it to the OpenAI-compatible `/v1/` endpoint of your model server:

```bash
docker run -p 8000:8000 --name customs-ai-container \
  -e LLM_BASE_URL=http://host.docker.internal:8080/v1/ \
  customs-ai-backend
```

- **Model served on the host:** use `http://host.docker.internal:8080/v1/`
  (or `http://172.17.0.1:8080/v1/` on Linux, which the backend also tries as a
  fallback).
- **Model in another container on the same Docker network:** use the container
  name, e.g. `http://vllm:80/v1/` or `http://tgi:80/v1/`.

The [`run_stack.bash`](run_stack.bash) script automates this wiring end to end:
`./run_stack.bash` (vLLM by default) or `./run_stack.bash tgi`.

### 4. Accessing the API

Once the container is running, you can access the health check endpoint to verify it's working:

`http://localhost:8000/api/v1/health-check`

You can also interact with other endpoints, such as the declaration analyzer:

`POST http://localhost:8000/api/v1/analyze-declaration`

### Authentication

Data endpoints are protected by an optional API key. When `ADMIN_API_KEY` is set,
every request (except `/health-check`) must include it in the `X-API-Key` header:

```bash
curl -H "X-API-Key: $ADMIN_API_KEY" http://localhost:8000/api/v1/analyze-declaration
```

If `ADMIN_API_KEY` is left blank, authentication is disabled — convenient for
local development, but set a key for any shared deployment.

### Stopping and Removing the Container

- **To stop the container:**
  ```bash
  docker stop customs-ai-container
  ```

- **To remove the stopped container:**
  ```bash
  docker rm customs-ai-container
  ```