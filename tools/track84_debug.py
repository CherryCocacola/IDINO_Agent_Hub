"""트랙 #84 디버그 — API 응답 구조 확인."""
import json
import sys
import io
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://192.168.10.39:64005"
EMAIL = "admin@example.com"
PASSWORD = "Admin123!"


def req(method, path, *, headers=None, body=None, timeout=15):
    url = BASE + path
    data = json.dumps(body).encode("utf-8") if body else None
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    if body:
        h["Content-Type"] = "application/json"
    rq = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(rq, timeout=timeout) as r:
            return r.getcode(), r.read().decode("utf-8", errors="replace")
    except Exception as e:
        try:
            text = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        except Exception:
            text = ""
        code = getattr(e, "code", -1)
        return code, f"EXC:{type(e).__name__}:{e} :: {text}"


# Login
code, text = req("POST", "/api/auth/login", body={"email": EMAIL, "password": PASSWORD})
print(f"=== LOGIN: status={code}")
token = json.loads(text)["token"]
h = {"Authorization": f"Bearer {token}"}

# /api/agents
print("\n=== /api/agents")
code, text = req("GET", "/api/agents", headers=h)
print(f"status={code}")
try:
    agents = json.loads(text)
    if isinstance(agents, list):
        print(f"count: {len(agents)}")
        if agents:
            print("first agent keys:", list(agents[0].keys())[:30])
            print("first agent (sample):", {k: agents[0].get(k) for k in ["agentId", "AgentId", "agentName", "agentCode", "isActive", "llmRouting", "isPublic", "serviceId"]})
    else:
        print(f"not a list: type={type(agents).__name__} :: {str(agents)[:200]}")
except Exception as e:
    print(f"parse error: {e}")
    print(f"body[:500]: {text[:500]}")

# /api/api-services
print("\n=== /api/api-services")
code, text = req("GET", "/api/api-services", headers=h)
print(f"status={code}")
try:
    svcs = json.loads(text)
    if isinstance(svcs, list):
        print(f"count: {len(svcs)}")
        if svcs:
            print("first service keys:", list(svcs[0].keys())[:30])
            print("services:", [{k: s.get(k) for k in ["serviceId", "ServiceId", "serviceCode", "ServiceCode", "serviceName"]} for s in svcs[:10]])
except Exception as e:
    print(f"parse error: {e}")
    print(f"body[:500]: {text[:500]}")

# /api/api-keys
print("\n=== /api/api-keys")
code, text = req("GET", "/api/api-keys", headers=h)
print(f"status={code}")
try:
    keys = json.loads(text)
    if isinstance(keys, list):
        print(f"count: {len(keys)}")
        if keys:
            print("first key keys:", list(keys[0].keys())[:30])
except Exception as e:
    print(f"parse error: {e}")
    print(f"body[:500]: {text[:500]}")

# /api/tools
print("\n=== /api/tools")
code, text = req("GET", "/api/tools", headers=h)
print(f"status={code} :: {text[:500]}")

# /v1/models (X-API-Key 없이 - anon)
print("\n=== /v1/models (anon)")
code, text = req("GET", "/v1/models")
print(f"status={code} :: {text[:200]}")
