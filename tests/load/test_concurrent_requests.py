"""
Load testing script for validating 100 concurrent request target.
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Any


async def make_request(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    """Make a single HTTP request."""
    start = time.time()
    try:
        async with session.get(url) as response:
            await response.read()
            latency = time.time() - start
            return {
                "status": response.status,
                "latency": latency,
                "success": response.status == 200
            }
    except Exception as e:
        return {
            "status": 0,
            "latency": time.time() - start,
            "success": False,
            "error": str(e)
        }


async def load_test(base_url: str, num_requests: int = 100, concurrency: int = 100):
    """
    Run load test with concurrent requests.
    
    Args:
        base_url: Base URL of the API
        num_requests: Total number of requests
        concurrency: Number of concurrent requests
    """
    url = f"{base_url}/health"
    
    async with aiohttp.ClientSession() as session:
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_request():
            async with semaphore:
                return await make_request(session, url)
        
        # Run all requests
        start_time = time.time()
        tasks = [bounded_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Analyze results
        successful = sum(1 for r in results if r["success"])
        failed = num_requests - successful
        latencies = [r["latency"] for r in results if r["success"]]
        
        if latencies:
            latencies.sort()
            p50 = latencies[int(len(latencies) * 0.50)]
            p95 = latencies[int(len(latencies) * 0.95)]
            p99 = latencies[int(len(latencies) * 0.99)]
        else:
            p50 = p95 = p99 = 0
        
        print(f"\nLoad Test Results:")
        print(f"Total Requests: {num_requests}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Requests/sec: {num_requests / total_time:.2f}")
        print(f"P50 Latency: {p50*1000:.2f}ms")
        print(f"P95 Latency: {p95*1000:.2f}ms")
        print(f"P99 Latency: {p99*1000:.2f}ms")
        
        # Validate targets
        assert successful >= 100, f"Only {successful} requests succeeded, need 100+"
        assert p95 < 3.0, f"P95 latency {p95}s exceeds 3s target"
        print("\n✓ Load test passed: 100+ concurrent requests handled")


if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    asyncio.run(load_test(base_url, num_requests=100, concurrency=100))

