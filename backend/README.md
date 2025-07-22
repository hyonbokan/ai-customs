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

### 3. Connecting to a TGI Service

Since your TGI service runs separately, you must provide its URL to the backend container via an environment variable.

```bash
sudo docker run --gpus all -v ~/models/gemma-3-27b-it:/models/gemma-3-27b-it -p 8080:80 ghcr.io/huggingface/text-generation-inference:latest --model-id /models/gemma-3-27b-it --trust-remote-code --num-shard 2
```

Replace `<your_tgi_service_ip_or_hostname>` with the actual IP address or hostname where your TGI service is accessible. If both containers are running on the same machine with Docker, you might use `http://host.docker.internal:8080/v1/` or the machine's local IP address.

### 4. Accessing the API

Once the container is running, you can access the health check endpoint to verify it's working:

`http://localhost:8000/api/v1/health-check`

You can also interact with other endpoints, such as the declaration analyzer:

`POST http://localhost:8000/api/v1/analyze-declaration`

### Stopping and Removing the Container

- **To stop the container:**
  ```bash
  docker stop customs-ai-container
  ```

- **To remove the stopped container:**
  ```bash
  docker rm customs-ai-container
  ```