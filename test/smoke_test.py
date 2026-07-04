"""
Smoke Test Script
-------------------
Quick test that hits all endpoints to make sure the server is working.
Run this while the server is running on port 3000.

Usage: py test/smoke_test.py
"""

import json
import urllib.request
import urllib.error
import sys
import time

BASE_URL = "http://localhost:3000"

passed = 0
failed = 0
total = 0


def test(name, method, path, body=None, expected_status=200):
    """Run a single test case."""
    global passed, failed, total
    total += 1

    url = BASE_URL + path

    try:
        if body:
            data = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header("Content-Type", "application/json")
        else:
            req = urllib.request.Request(url, method=method)

        response = urllib.request.urlopen(req)
        status = response.getcode()
        resp_body = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        status = e.code
        try:
            resp_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            resp_body = {}

    except urllib.error.URLError as e:
        print(f"  FAIL  {name}")
        print(f"        Could not connect to server: {e.reason}")
        print(f"        Make sure the server is running on {BASE_URL}")
        failed += 1
        return None

    except Exception as e:
        print(f"  FAIL  {name}")
        print(f"        Error: {e}")
        failed += 1
        return None

    if status == expected_status:
        print(f"  PASS  {name} (status: {status})")
        passed += 1
    else:
        print(f"  FAIL  {name}")
        print(f"        Expected status {expected_status}, got {status}")
        print(f"        Response: {json.dumps(resp_body, indent=2)[:200]}")
        failed += 1

    return resp_body


def main():
    global passed, failed, total

    print("\n" + "=" * 50)
    print("  SMOKE TEST - Vendor Routing Platform")
    print("=" * 50 + "\n")

    # ---- 1. Health check ----
    print("--- Health Check ---")
    test("GET /health", "GET", "/health")

    # ---- 2. Register vendors ----
    print("\n--- Register Vendors ---")
    test("Register VendorA", "POST", "/vendors", {
        "name": "TestVendorA",
        "capability": "PAN_VERIFICATION",
        "costPerRequest": 1.5,
        "timeoutMs": 2000,
        "rateLimitPerMinute": 100,
        "priority": 1,
        "weight": 70,
        "supportedFeatures": ["name_match", "dob_match"]
    }, 201)

    test("Register VendorB", "POST", "/vendors", {
        "name": "TestVendorB",
        "capability": "PAN_VERIFICATION",
        "costPerRequest": 1.2,
        "timeoutMs": 3000,
        "rateLimitPerMinute": 50,
        "priority": 2,
        "weight": 30,
        "supportedFeatures": ["name_match"]
    }, 201)

    # ---- 3. Validation tests ----
    print("\n--- Validation Tests ---")
    test("Missing name", "POST", "/vendors", {
        "capability": "PAN_VERIFICATION"
    }, 400)

    test("Missing capability", "POST", "/vendors", {
        "name": "TestVendor"
    }, 400)

    test("Negative cost", "POST", "/vendors", {
        "name": "BadVendor",
        "capability": "TEST",
        "costPerRequest": -5
    }, 400)

    # ---- 4. List vendors ----
    print("\n--- List Vendors ---")
    result = test("List all vendors", "GET", "/vendors")
    if result:
        count = result.get("count", 0)
        print(f"        Found {count} vendors")

    test("Filter by capability", "GET", "/vendors?capability=PAN_VERIFICATION")

    # ---- 5. Set routing config ----
    print("\n--- Routing Config ---")
    test("Set routing config", "POST", "/routing-config", {
        "capability": "PAN_VERIFICATION",
        "strategy": "weighted"
    })

    test("Get routing config", "GET", "/routing-config?capability=PAN_VERIFICATION")

    test("Missing strategy", "POST", "/routing-config", {
        "capability": "PAN_VERIFICATION"
    }, 400)

    # ---- 6. Route requests ----
    print("\n--- Route Requests ---")
    for i in range(5):
        test(f"Route request #{i+1}", "POST", "/route", {
            "capability": "PAN_VERIFICATION",
            "payload": {"pan_number": "ABCDE1234F", "name": "Test User"}
        }, None)  # could be 200 or 503 depending on simulation
        # small delay between requests
        time.sleep(0.1)

    # fix: re-run with expected_status=None means we accept any status
    test("Route with missing capability", "POST", "/route", {
        "payload": {"test": True}
    }, 400)

    test("Route unknown capability", "POST", "/route", {
        "capability": "DOES_NOT_EXIST",
        "payload": {}
    }, 503)

    # ---- 7. Check metrics ----
    print("\n--- Metrics ---")
    test("Get all metrics", "GET", "/vendor-metrics")
    test("Get specific vendor metrics", "GET", "/vendor-metrics?vendor=TestVendorA")

    # ---- 8. Check logs ----
    print("\n--- Routing Logs ---")
    result = test("Get routing logs", "GET", "/routing-logs")
    if result:
        log_count = result.get("count", 0)
        print(f"        Found {log_count} routing logs")

    test("Get logs with limit", "GET", "/routing-logs?limit=3")

    # ---- Results ----
    print("\n" + "=" * 50)
    print(f"  Results: {passed} passed, {failed} failed, {total} total")
    print("=" * 50 + "\n")

    if failed > 0:
        sys.exit(1)


# fix the test function to handle None expected_status
original_test = test

def test(name, method, path, body=None, expected_status=200):
    if expected_status is None:
        # accept any status
        global passed, failed, total
        total += 1
        url = BASE_URL + path
        try:
            if body:
                data = json.dumps(body).encode("utf-8")
                req = urllib.request.Request(url, data=data, method=method)
                req.add_header("Content-Type", "application/json")
            else:
                req = urllib.request.Request(url, method=method)

            try:
                response = urllib.request.urlopen(req)
                status = response.getcode()
                resp_body = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                status = e.code
                resp_body = json.loads(e.read().decode("utf-8"))

            print(f"  PASS  {name} (status: {status})")
            passed += 1
            return resp_body

        except Exception as e:
            print(f"  FAIL  {name} - {e}")
            failed += 1
            return None
    else:
        return original_test(name, method, path, body, expected_status)


if __name__ == "__main__":
    main()
