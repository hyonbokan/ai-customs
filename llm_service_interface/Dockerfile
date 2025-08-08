FROM ghcr.io/huggingface/text-generation-inference:latest

LABEL maintainer="admin <admin@your.org>" \
      description="TGI Runtime Container - Models mounted via volumes" \
      version="1.0.0"

# Install minimal required tools
USER root
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Create model mount point with proper permissions
RUN mkdir -p /opt/models && chown -R 1000:1000 /opt/models

# Switch back to user
USER 1000

# Set working directory
WORKDIR /opt/models

# Environment variables for TGI configuration
ENV TGI_HOST="0.0.0.0"
ENV TGI_PORT="8080"
ENV TGI_NUM_SHARD="auto"
ENV TGI_MAX_CONCURRENT_REQUESTS="128"
ENV TGI_MAX_BEST_OF="2"
ENV TGI_MAX_STOP_SEQUENCES="4"
ENV TGI_MAX_INPUT_LENGTH="4096"
ENV TGI_MAX_TOTAL_TOKENS="8192"
ENV TGI_WAITING_SERVED_RATIO="1.2"
ENV TGI_MAX_BATCH_PREFILL_TOKENS="4096"
ENV TGI_MAX_BATCH_TOTAL_TOKENS="8192"
ENV TGI_TRUST_REMOTE_CODE="true"

# Runtime configuration
ENV MODEL_PATH="/opt/models"
ENV TGI_LOG_LEVEL="INFO"

# Expose TGI port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5m --retries=3 \
  CMD curl -f http://localhost:${TGI_PORT}/health || exit 1

# Copy entrypoint script
COPY --chown=1000:1000 entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

ENTRYPOINT ["/opt/entrypoint.sh"]