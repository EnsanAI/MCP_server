#!/bin/bash
# Quick local runner for MCP server (no Docker)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting MCP Server Locally..."
echo ""

# Check if db-ops is running
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✓ db-ops is accessible at http://localhost:8001"
else
    echo "⚠️  Warning: db-ops not accessible at http://localhost:8001"
    echo "   Make sure db-ops service is running:"
    echo "   cd .. && docker-compose -f docker-compose.local.yml up -d db-ops"
    echo ""
fi

# Set environment variables
export DB_OPS_URL=http://localhost:8001
export ADMIN_ACCESS_TOKEN=${ADMIN_ACCESS_TOKEN:-local_test_admin_token}
export MCP_MODE=sse
export PORT=8000
export HOST=0.0.0.0

echo "Environment:"
echo "  DB_OPS_URL: $DB_OPS_URL"
echo "  MCP_MODE: $MCP_MODE"
echo "  PORT: $PORT"
echo ""

# Check if dependencies are installed
if ! python -c "import fastmcp" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

echo "🎯 Starting MCP Server..."
echo "   Access at: http://localhost:8000"
echo "   SSE endpoint: http://localhost:8000/sse"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main.py
