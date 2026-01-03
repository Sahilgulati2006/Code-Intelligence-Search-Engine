#!/usr/bin/env python3
"""
Focused test for authentication enforcement
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Test 1: Auth disabled (default)
print("=" * 70)
print("AUTH TEST 1: AUTH DISABLED (DEFAULT)")
print("=" * 70)

os.environ["AUTH_ENABLED"] = "false"

from app.main import app as app1
from fastapi.testclient import TestClient

client1 = TestClient(app1)

response = client1.post("/index", json={"repo_url": "https://github.com/test/repo"})
print(f"\n/index WITHOUT API key (AUTH_DISABLED):")
print(f"  Status: {response.status_code}")
print(f"  Response: {response.json()}")

if response.status_code == 202:
    print("  ✅ CORRECT - Request accepted (202 = job queued)")
else:
    print(f"  ⚠️  Got {response.status_code} (expected 202)")


# Test 2: Auth enabled
print("\n" + "=" * 70)
print("AUTH TEST 2: AUTH ENABLED")
print("=" * 70)

os.environ["AUTH_ENABLED"] = "true"
os.environ["API_KEYS"] = '{"admin": "secret"}'

# Clear the module cache and reload
import sys
for mod in list(sys.modules.keys()):
    if mod.startswith('app'):
        del sys.modules[mod]

from app.main import app as app2
client2 = TestClient(app2)

response = client2.post("/index", json={"repo_url": "https://github.com/test/repo"})
print(f"\n/index WITHOUT API key (AUTH_ENABLED):")
print(f"  Status: {response.status_code}")
print(f"  Response: {response.json()}")

if response.status_code in [401, 403]:
    print(f"  ✅ CORRECT - Request rejected ({response.status_code})")
elif response.status_code == 202:
    print(f"  ⚠️  Got 202 - Auth check may not be enforced")
else:
    print(f"  ⚠️  Got {response.status_code} (unexpected)")

# Test 3: With API key
response = client2.post(
    "/index",
    json={"repo_url": "https://github.com/test/repo"},
    headers={"X-API-Key": "admin:secret"}
)
print(f"\n/index WITH valid API key (AUTH_ENABLED):")
print(f"  Status: {response.status_code}")
print(f"  Response: {response.json()}")

if response.status_code == 202:
    print(f"  ✅ CORRECT - Request accepted (202 = job queued)")
else:
    print(f"  ⚠️  Got {response.status_code} (expected 202)")

print("\n" + "=" * 70)
