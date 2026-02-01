# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (gcc for python packages, curl for healthcheck)
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the MCP server runs on (FastMCP default is usually stdio, but for SSE we need a port)
# We will use SSE mode for Docker compatibility
ENV MCP_MODE=sse
EXPOSE 8000

# Run the server
CMD ["fastmcp", "run", "main.py", "--transport", "sse", "--port", "8000", "--host", "0.0.0.0"]