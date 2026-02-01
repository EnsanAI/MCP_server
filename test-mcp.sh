#!/bin/bash
# MCP Server Test Runner for Docker Environment
# This script runs the MCP test suite inside the Docker container

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MCP Server Test Runner${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose not found${NC}"
    exit 1
fi

# Navigate to the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check if MCP container is running
if ! docker ps | grep -q "carebot-mcp-server-local"; then
    echo -e "${YELLOW}MCP server container is not running${NC}"
    echo -e "${BLUE}Starting MCP server...${NC}"
    docker-compose -f docker-compose.local.yml up -d mcp-server

    # Wait for container to be healthy
    echo -e "${BLUE}Waiting for MCP server to be healthy...${NC}"
    for i in {1..30}; do
        if docker ps | grep "carebot-mcp-server-local" | grep -q "(healthy)"; then
            echo -e "${GREEN}✓ MCP server is healthy${NC}"
            break
        fi
        echo -n "."
        sleep 2
        if [ $i -eq 30 ]; then
            echo -e "${RED}Timeout waiting for MCP server to be healthy${NC}"
            echo -e "${YELLOW}Check logs: docker logs carebot-mcp-server-local${NC}"
            exit 1
        fi
    done
else
    echo -e "${GREEN}✓ MCP server is already running${NC}"
fi

# Check if db-ops is running
if ! docker ps | grep -q "carebot-db-ops-local"; then
    echo -e "${RED}Error: db-ops container is not running${NC}"
    echo -e "${YELLOW}Start it with: docker-compose -f docker-compose.local.yml up -d db-ops${NC}"
    exit 1
fi

echo -e "${GREEN}✓ db-ops is running${NC}"

# Run the test script inside the container
echo -e "${BLUE}Running MCP test suite...${NC}"
echo ""

docker exec -it carebot-mcp-server-local python /app/Test/test_mcp_docker.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  All tests completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  Some tests failed!${NC}"
    echo -e "${RED}========================================${NC}"
fi

exit $exit_code
