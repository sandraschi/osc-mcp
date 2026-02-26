# OSC-MCP Dockerfile
# Multi-stage build for optimal image size

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install -e ".[dev]"

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    # Required for audio/MIDI libraries
    libasound2-dev \
    libjack-dev \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r oscmcp && useradd -r -g oscmcp oscmcp

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy source code
COPY src/ ./src/

# Change ownership to non-root user
RUN chown -R oscmcp:oscmcp /app

# Switch to non-root user
USER oscmcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import oscmcp.server; print('OK')" || exit 1

# Expose port for HTTP transport (optional)
EXPOSE 8000

# Default command
CMD ["python", "-m", "oscmcp.server"]