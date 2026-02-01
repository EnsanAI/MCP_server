import os
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("dbops-mcp.dependencies")

class DBOpsClient:
    def __init__(self):
        self.base_url = os.getenv("DB_OPS_URL", "http://localhost:3000").rstrip('/')
        self.token = os.getenv("ADMIN_ACCESS_TOKEN")
        
        # 1. Persistent Headers
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Connection": "keep-alive" # Hint to keep the socket open
        }
        
        # 2. Optimized Client (Shared across all requests)
        # We use a long-lived client with a connection pool
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            # Limits: Keep up to 20 idle connections open for reuse
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
            # Timeout: Fail fast if DBOps is struggling
            timeout=httpx.Timeout(15.0, connect=5.0)
        )

    async def get(self, endpoint: str, params=None):
        """High-efficiency GET using pooled connections."""
        try:
            res = await self._client.get(endpoint, params=params)
            res.raise_for_status()
            return res.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"DBOps GET Error: {e.response.status_code} at {endpoint}")
            raise

    async def post(self, endpoint: str, data: dict):
        """High-efficiency POST using pooled connections."""
        try:
            res = await self._client.post(endpoint, json=data)
            res.raise_for_status()
            return res.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"DBOps POST Error: {e.response.status_code} at {endpoint}")
            raise

    # Added PUT and DELETE for complete medication management
    async def put(self, endpoint: str, data: dict):
        res = await self._client.put(endpoint, json=data)
        res.raise_for_status()
        return res.json()

    async def patch(self, endpoint: str, data: dict):
        """PATCH request to DBOps API for partial updates."""
        try:
            res = await self._client.patch(endpoint, json=data)
            res.raise_for_status()
            return res.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"DBOps PATCH Error: {e.response.status_code} at {endpoint}")
            raise

    async def close(self):
        """Gracefully shut down the connection pool."""
        await self._client.aclose()

# Global instance
dbops = DBOpsClient()