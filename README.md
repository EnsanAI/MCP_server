# CareBot-DBOps-MCP

High-Scale Model Context Protocol (MCP) Server for DBOps

CareBot-DBOps-MCP is a production-grade integration layer designed to bridge the gap between large-scale enterprise APIs (110+ endpoints) and LLM agents. Built on the "Dynamic Capability Injection" pattern, it ensures that AI models remain performant and accurate without exhausting their context windows.

## Key Features

*   **Dynamic Capability Architecture**: Implements a "Dynamic Capability" pattern. Instead of overloading the LLM with 110+ tools, it provides a meta-search tool that injects only relevant capabilities based on intent.
*   **Context Enrichment**: Built-in "Translation Layer" that automatically resolves human-readable names (e.g., "Dr. Smith") into database UUIDs in real-time.
*   **High-Efficiency Networking**: Utilizes httpx connection pooling to maintain "warm" TCP sockets, reducing latency between the MCP and DBOps by 60-80%.
*   **Modular API Taxonomy**: Logic is divided into 8 specialized "API Families" for better maintainability and cleaner execution.

## API Family Taxonomy

*   **Doctors**: Staff registry, scheduling, and real-time availability.
*   **Patients**: Medical records, demographic data, and history.
*   **Appointments**: Bridge logic for booking, rescheduling, and cancellations.
*   **Reminders**: Medication adherence tracking and automated notifications.
*   **Medications**: Prescriptions, refill management, and historical logs.
*   **Clinical**: SOAP Notes, versioning, and treatment plan management.
*   **Analytics**: Revenue tracking, performance dashboards, and trends.
*   **Ops**: Clinic management and pre-visit patient questionnaires.

## Technical Stack

*   **Core**: Python 3.11+
*   **Framework**: FastMCP
*   **Transport**: SSE (Server-Sent Events) via Uvicorn
*   **Database Client**: Optimized httpx with persistent connection pooling
*   **Containerization**: Docker with hot-reload volume mapping

## Setup & Installation

### 1. Environment Configuration

Create a `.env` file in the root directory:

```bash
DB_OPS_URL=http://localhost:3000
ADMIN_ACCESS_TOKEN=your_persistent_admin_token
```

### 2. Docker Deployment

#### Option A: Standalone Docker Container

The server can run as a standalone container:

```bash
docker build -t mcp_server .

docker run -d \
  --name mcp_server \
  -p 8000:8000 \
  -v ${PWD}:/app \
  --env-file .env \
  mcp_server
```

#### Option B: Docker Compose (Recommended)

The MCP server is integrated into the main CareBot docker-compose.local.yml file. To run it with all other services:

```bash
# From the carebot_dev root directory
docker-compose -f docker-compose.local.yml up -d mcp-server

# Or to start all services including MCP
docker-compose -f docker-compose.local.yml up -d
```

The service will be available at:
- **Local**: http://localhost:8003
- **Container network**: http://mcp-server:8000

**Environment Variables** (set in docker-compose.local.yml):
- `DB_OPS_URL`: URL to the db-ops service (default: http://db-ops:3000)
- `ADMIN_ACCESS_TOKEN`: Admin token for DBOps authentication
- `MCP_MODE`: Transport mode (set to "sse" for Server-Sent Events)
- `PORT`: Internal port (8000)
- `HOST`: Bind address (0.0.0.0)

## Testing

### Automated Test Suite

A comprehensive test suite is provided to verify MCP tools against the db-ops service:

```bash
# From the MCP_server directory
./test-mcp.sh
```

The test script will:
1. Check if MCP server is running (starts it if needed)
2. Verify db-ops connectivity
3. Test all MCP tool categories:
   - Patient tools (resolution, details, appointments)
   - Doctor tools (resolution, details, availability)
   - Appointment tools
   - Clinic tools
   - Medication tools
4. Provide colored output with pass/fail/warning status
5. Generate a test summary with success rate

**Manual Testing from Container:**

```bash
# Run tests directly inside the container
docker exec -it carebot-mcp-server-local python /app/Test/test_mcp_docker.py
```

### Verification & Latency Testing

Verify the SSE stream and internal latency:

```bash
# Verify SSE Pipe (from host)
time curl -s http://localhost:8003/sse

# From inside the container network
docker exec carebot-mcp-server-local curl -s http://localhost:8000/sse

# Run System Health Check
curl -X POST http://localhost:8003/messages/?session_id=test_session \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "check_system_health", "arguments": {}}}'
```

### Test Environment Variables

The test suite uses these environment variables (automatically configured in docker-compose):
- `DB_OPS_URL`: http://db-ops:3000
- `ADMIN_ACCESS_TOKEN`: Retrieved from environment or defaults to local_test_admin_token

## Internal Architecture: Circular Dependency Fix

To handle the scale of 8 interconnected families, this project utilizes Local Import Injection.

*   **Problem**: High-dependency tools (like `previsit.py`) often require helper functions from `appointments.py`, which in turn import `patients.py`.
*   **Solution**: Helper imports are performed inside the tool functions. This ensures the server starts instantly and dependencies are only resolved at the moment of execution.

## Roadmap

*   **Parallel Resolution**: Moving `asyncio.gather` into multi-ID resolution tools for sub-50ms execution.
*   **PatientAI Integration**: Direct SSE-to-SSE bridge for real-time medical reasoning.
*   **Vector Search**: Replacing keyword search in the capability tool with semantic vector embeddings.