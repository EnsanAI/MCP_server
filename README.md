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

The server is designed to run in a containerized environment to ensure parity with DBOps:

```powershell
docker build -t mcp_server .

docker run -d `
  --name mcp_server `
  -p 8000:8000 `
  -v ${PWD}:/app `
  --env-file .env `
  mcp_server
```

## Verification & Latency Testing

Verify the SSE stream and internal latency using Bash:

```bash
# Verify SSE Pipe
time curl -s http://localhost:8000/sse

# Run System Health Check
curl -X POST http://localhost:8000/messages/?session_id=YOUR_ID \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "check_system_health", "arguments": {}}}'
```

## Internal Architecture: Circular Dependency Fix

To handle the scale of 8 interconnected families, this project utilizes Local Import Injection.

*   **Problem**: High-dependency tools (like `previsit.py`) often require helper functions from `appointments.py`, which in turn import `patients.py`.
*   **Solution**: Helper imports are performed inside the tool functions. This ensures the server starts instantly and dependencies are only resolved at the moment of execution.

## Roadmap

*   **Parallel Resolution**: Moving `asyncio.gather` into multi-ID resolution tools for sub-50ms execution.
*   **PatientAI Integration**: Direct SSE-to-SSE bridge for real-time medical reasoning.
*   **Vector Search**: Replacing keyword search in the capability tool with semantic vector embeddings.