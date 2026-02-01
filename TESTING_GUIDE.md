# MCP Server Testing Guide

## Quick Start

### 1. Start the MCP Service

```bash
# From the carebot_dev root directory
cd /Users/omar/Downloads/The\ Future/carebot_dev

# Start MCP server (will also start db-ops if not running)
docker-compose -f docker-compose.local.yml up -d mcp-server
```

### 2. Run the Test Suite

```bash
# From the MCP_server directory
cd MCP_server
./test-mcp.sh
```

## What Gets Tested

The test suite validates:

### ✅ Environment Configuration
- DB_OPS_URL is set correctly
- ADMIN_ACCESS_TOKEN is available

### ✅ DB-Ops Connectivity
- Connection to db-ops service
- Basic API endpoint access

### ✅ Patient Tools
- Fetching all patients
- Resolving patient by name (name → UUID)
- Fetching patient details
- Fetching patient appointments

### ✅ Doctor Tools
- Fetching all doctors
- Resolving doctor by name (name → UUID)
- Fetching doctor details
- Fetching doctor availability

### ✅ Appointment Tools
- Fetching all appointments
- Fetching appointment details

### ✅ Clinic Tools
- Fetching all clinics
- Fetching clinic details

### ✅ Medication Tools
- Fetching patient medications
- Resolving medication by name for a patient

## Understanding Test Output

### Status Indicators

- **✓ PASS** (Green): Test passed successfully
- **✗ FAIL** (Red): Test failed - requires attention
- **⚠ WARN** (Yellow): Test couldn't complete due to missing data (not a failure)

### Example Output

```
╔═══════════════════════════════════════════════════════════╗
║         MCP SERVER TEST SUITE - DOCKER ENVIRONMENT        ║
╚═══════════════════════════════════════════════════════════╝

============================================================
ENVIRONMENT CONFIGURATION
============================================================
✓ DB_OPS_URL configured ... PASS
  → URL: http://db-ops:3000
✓ ADMIN_ACCESS_TOKEN configured ... PASS
  → Token is set

============================================================
DB-OPS CONNECTIVITY
============================================================
✓ Connect to db-ops /clinics endpoint ... PASS
  → Found 5 clinics

============================================================
TEST SUMMARY
============================================================
Passed: 15
Failed: 0
Warnings: 2
Success Rate: 88.2%
```

## Manual Testing

### Test Individual Components

```bash
# Enter the container
docker exec -it carebot-mcp-server-local bash

# Run Python tests directly
python /app/Test/test_mcp_docker.py

# Test specific endpoints manually
python -c "
import asyncio
from dependencies import dbops
async def test():
    patients = await dbops.get('/patients')
    print(f'Found {len(patients)} patients')
    await dbops.close()
asyncio.run(test())
"
```

### Test SSE Endpoint

```bash
# From host machine
curl -I http://localhost:8003/sse

# Should return:
# HTTP/1.1 200 OK
# content-type: text/event-stream
```

### Test Health Check

```bash
# Using the check_system_health tool
curl -X POST http://localhost:8003/messages/?session_id=test \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "check_system_health",
      "arguments": {}
    }
  }'
```

## Troubleshooting

### MCP Server Won't Start

```bash
# Check container logs
docker logs carebot-mcp-server-local

# Check if port 8003 is available
lsof -i :8003

# Rebuild the container
docker-compose -f docker-compose.local.yml build mcp-server
docker-compose -f docker-compose.local.yml up -d mcp-server
```

### Connection to db-ops Fails

```bash
# Verify db-ops is running
docker ps | grep db-ops

# Check db-ops health
docker exec carebot-db-ops-local wget -O- http://localhost:3000/health

# Verify network connectivity
docker exec carebot-mcp-server-local curl http://db-ops:3000/clinics
```

### Tests Show Warnings

Warnings (⚠) are typically not failures. Common causes:
- No data in database (e.g., no appointments, no medications)
- Optional features not configured
- Test data doesn't match expected patterns

### Permission Errors

```bash
# Make test script executable
chmod +x test-mcp.sh

# If ADMIN_ACCESS_TOKEN is missing, check .env file
docker-compose -f docker-compose.local.yml config | grep ADMIN
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_OPS_URL` | `http://db-ops:3000` | URL to db-ops service |
| `ADMIN_ACCESS_TOKEN` | `local_test_admin_token` | Admin authentication token |
| `MCP_MODE` | `sse` | Transport mode (Server-Sent Events) |
| `PORT` | `8000` | Internal container port |
| `HOST` | `0.0.0.0` | Bind address |

## Service URLs

| Service | Internal (Container) | External (Host) |
|---------|---------------------|-----------------|
| MCP Server | `http://mcp-server:8000` | `http://localhost:8003` |
| DB-Ops | `http://db-ops:3000` | `http://localhost:8001` |
| Postgres | `postgres:5432` | `localhost:5432` |

## Advanced Testing

### Performance Testing

```bash
# Measure connection latency
docker exec carebot-mcp-server-local bash -c "
time python -c '
import asyncio
from dependencies import dbops
async def test():
    await dbops.get(\"/clinics\")
    await dbops.close()
asyncio.run(test())
'
"
```

### Load Testing

```bash
# Run multiple concurrent requests
for i in {1..10}; do
    docker exec carebot-mcp-server-local python /app/Test/test_mcp_docker.py &
done
wait
```

### Cache Testing

The MCP server uses a 10-minute TTL cache for patient data. To test cache effectiveness:

```bash
# First call (cache miss)
time docker exec carebot-mcp-server-local python -c "
import asyncio
from tools.patients import resolve_patient_id
async def test():
    await resolve_patient_id('Test Patient')
asyncio.run(test())
"

# Second call (cache hit - should be faster)
time docker exec carebot-mcp-server-local python -c "
import asyncio
from tools.patients import resolve_patient_id
async def test():
    await resolve_patient_id('Test Patient')
asyncio.run(test())
"
```

## Next Steps

After successful testing:

1. **Integration Testing**: Test MCP server with patient-ai-service-v3
2. **Production Deployment**: Update production docker-compose with MCP service
3. **Monitoring**: Add logging and metrics collection
4. **Documentation**: Document MCP tools for AI agents to consume
