import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class DBOpsClient:
    def __init__(self):
        self.base_url = os.getenv("DB_OPS_URL", "http://localhost:3000")# need to change this to the actual URL later
        self.token = os.getenv("ADMIN_ACCESS_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    async def get(self, endpoint: str, params=None):
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{self.base_url}{endpoint}", headers=self.headers, params=params)
            res.raise_for_status()
            return res.json()

    async def post(self, endpoint: str, data: dict):
        async with httpx.AsyncClient() as client:
            res = await client.post(f"{self.base_url}{endpoint}", headers=self.headers, json=data)
            res.raise_for_status()
            return res.json()

dbops = DBOpsClient()