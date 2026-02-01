#!/bin/bash
# Test MCP server running locally (not in Docker)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧪 Testing MCP Server (Local Mode)..."
echo ""

# Set environment variables to match local setup
export DB_OPS_URL=http://localhost:8001
export ADMIN_ACCESS_TOKEN=${ADMIN_ACCESS_TOKEN:-local_test_admin_token}

# Check if db-ops is accessible
if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "❌ Error: db-ops is not accessible at http://localhost:8001"
    echo ""
    echo "Start db-ops first:"
    echo "  cd .. && docker-compose -f docker-compose.local.yml up -d db-ops"
    exit 1
fi

echo "✓ db-ops is accessible"
echo ""

# Run the test suite
python Test/test_mcp_docker.py

exit $?
