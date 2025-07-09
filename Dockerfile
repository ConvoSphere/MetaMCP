# =============================================================================
# MCP Meta-Server Dockerfile
# =============================================================================

# Build Stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production Stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r metamcp && useradd -r -g metamcp metamcp

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/metamcp/.local

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/policies && \
    chown -R metamcp:metamcp /app

# Make sure scripts are executable
RUN chmod +x scripts/*.sh 2>/dev/null || true

# Set environment variables
ENV PATH=/home/metamcp/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER metamcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "-m", "metamcp.main"]