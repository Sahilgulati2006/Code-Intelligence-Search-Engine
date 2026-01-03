#!/usr/bin/env python3
"""
Runtime integration test for Phase 2
Tests with actual server running
"""

import subprocess
import time
import os
import sys
import json
import requests
from pathlib import Path

BACKEND_PATH = Path(__file__).parent
VENV_PYTHON = "/Users/sahilgulati/Desktop/Weird projects/Code-Intelligence-Search-Engine/venv/bin/python"
PORT = 8002
BASE_URL = f"http://127.0.0.1:{PORT}"

def start_server(auth_enabled=False, rate_limit_enabled=False):
    """Start backend server with specific settings"""
    env = os.environ.copy()
    env["AUTH_ENABLED"] = "true" if auth_enabled else "false"
    env["RATE_LIMIT_ENABLED"] = "true" if rate_limit_enabled else "false"
    env["API_KEYS"] = '{"test": "secret123"}'
    env["RATE_LIMIT_REQUESTS"] = "5"
    env["RATE_LIMIT_WINDOW"] = "60"
    
    print(f"\n🚀 Starting server on port {PORT}")
    print(f"   AUTH_ENABLED={auth_enabled}, RATE_LIMIT_ENABLED={rate_limit_enabled}")
    
    process = subprocess.Popen(
        [VENV_PYTHON, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", f"--port", str(PORT)],
        cwd=str(BACKEND_PATH),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print(f"   ✅ Server started successfully")
            return process
    except:
        pass
    
    print(f"   ❌ Server failed to start")
    process.terminate()
    return None


def stop_server(process):
    """Stop the server"""
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
        except:
            process.kill()
        print(f"   ✅ Server stopped")


def test_auth_disabled():
    """Test with auth disabled (default)"""
    print("\n" + "=" * 70)
    print("TEST 1: AUTH DISABLED (Default Configuration)")
    print("=" * 70)
    
    process = start_server(auth_enabled=False)
    if not process:
        print("❌ Failed to start server")
        return False
    
    try:
        # Should work WITHOUT API key
        print("\n✓ Testing /index WITHOUT X-API-Key header:")
        response = requests.post(
            f"{BASE_URL}/index",
            json={"repo_url": "https://github.com/test/repo"},
            timeout=5
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        if response.status_code in [200, 202]:
            print("  ✅ Request accepted (auth disabled works)")
            return True
        else:
            print(f"  ❌ Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    finally:
        stop_server(process)


def test_auth_enabled():
    """Test with auth enabled"""
    print("\n" + "=" * 70)
    print("TEST 2: AUTH ENABLED")
    print("=" * 70)
    
    process = start_server(auth_enabled=True)
    if not process:
        print("❌ Failed to start server")
        return False
    
    try:
        # Should FAIL without API key
        print("\n✓ Testing /index WITHOUT X-API-Key header:")
        response = requests.post(
            f"{BASE_URL}/index",
            json={"repo_url": "https://github.com/test/repo"},
            timeout=5
        )
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 403 or response.status_code == 401:
            print(f"  ✅ Correctly rejected unauthorized request (status {response.status_code})")
            test1_passed = True
        else:
            print(f"  ⚠️  Got {response.status_code} (expected 401/403)")
            test1_passed = False
        
        # Should SUCCEED with correct API key
        print("\n✓ Testing /index WITH valid X-API-Key header:")
        response = requests.post(
            f"{BASE_URL}/index",
            json={"repo_url": "https://github.com/test/repo"},
            headers={"X-API-Key": "test:secret123"},
            timeout=5
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        if response.status_code in [200, 202]:
            print("  ✅ Correctly accepted authorized request")
            test2_passed = True
        else:
            print(f"  ❌ Unexpected status: {response.status_code}")
            test2_passed = False
        
        return test1_passed and test2_passed
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    finally:
        stop_server(process)


def test_rate_limiting():
    """Test rate limiting"""
    print("\n" + "=" * 70)
    print("TEST 3: RATE LIMITING")
    print("=" * 70)
    
    process = start_server(auth_enabled=False, rate_limit_enabled=True)
    if not process:
        print("❌ Failed to start server")
        return False
    
    try:
        print("\n✓ Making multiple requests to trigger rate limit:")
        
        for i in range(8):
            response = requests.post(
                f"{BASE_URL}/search",
                json={"query": f"test {i}", "top_k": 3, "repo_id": "test/repo"},
                timeout=5
            )
            print(f"  Request {i+1}: Status {response.status_code}", end="")
            
            if response.status_code == 429:
                print(" ← RATE LIMITED ✅")
                return True
            else:
                print()
        
        print("\n⚠️  Did not trigger rate limit after 8 requests")
        print("  (This may be normal if the limit is very high)")
        return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    finally:
        stop_server(process)


def test_search_endpoint():
    """Test search endpoint works"""
    print("\n" + "=" * 70)
    print("TEST 4: SEARCH ENDPOINT")
    print("=" * 70)
    
    process = start_server(auth_enabled=False)
    if not process:
        print("❌ Failed to start server")
        return False
    
    try:
        print("\n✓ Testing /search endpoint:")
        response = requests.post(
            f"{BASE_URL}/search",
            json={"query": "test", "top_k": 5, "repo_id": "test/repo"},
            timeout=5
        )
        print(f"  Status: {response.status_code}")
        data = response.json()
        print(f"  Response keys: {list(data.keys())}")
        
        if response.status_code == 200 and "results" in data:
            print(f"  ✅ Search endpoint works (got {len(data['results'])} results)")
            return True
        else:
            print(f"  ❌ Unexpected response")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    finally:
        stop_server(process)


if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 2 RUNTIME INTEGRATION TESTS")
    print("=" * 70)
    
    try:
        results = {
            "Test 1 (Auth Disabled)": test_auth_disabled(),
            "Test 2 (Auth Enabled)": test_auth_enabled(),
            "Test 3 (Rate Limiting)": test_rate_limiting(),
            "Test 4 (Search Endpoint)": test_search_endpoint(),
        }
        
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        all_passed = all(results.values())
        
        print("\n" + "=" * 70)
        if all_passed:
            print("🎉 ALL RUNTIME TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW ABOVE")
        print("=" * 70 + "\n")
        
        sys.exit(0 if all_passed else 1)
        
    except Exception as e:
        print(f"\n❌ TEST SUITE ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
