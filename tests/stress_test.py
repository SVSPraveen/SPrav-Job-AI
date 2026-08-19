import asyncio
import httpx
import time
import random

API_BASE = "http://127.0.0.1:8000/api"

async def post_job(client, i, auth_headers):
    payload = {
        "id": f"stress_job_{i}_{random.randint(1000, 9999)}",
        "title": f"Stress Test Engineer {i}",
        "company": "StressCorp",
        "url": f"https://example.com/job/{i}",
        "description": "Stress testing the SQLite database."
    }
    try:
        r = await client.post(f"{API_BASE}/jobs", headers=auth_headers, json=payload, timeout=20.0)
        return r.status_code
    except Exception as e:
        return str(e)

async def main():
    print("Fetching auth token...")
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/auto-login")
        if r.status_code != 200:
            print("Failed to auto-login. Check if backend is running.")
            return
            
        token = r.json().get("access_token")
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        print("Starting concurrency stress test (200 simultaneous POSTs)...")
        start = time.time()
        
        tasks = [post_job(client, i, auth_headers) for i in range(200)]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        
        status_counts = {}
        for r in results:
            status_counts[r] = status_counts.get(r, 0) + 1
            
        print(f"Test completed in {elapsed:.2f} seconds.")
        print("Result summary:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")

if __name__ == "__main__":
    asyncio.run(main())
