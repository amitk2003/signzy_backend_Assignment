# curl examples for Vendor Routing Platform

Start the server using `python app.py` on port 3000, then run these commands from another terminal.

---

### 1. Register a new vendor

```bash
curl -X POST http://localhost:3000/vendors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VendorZ",
    "capability": "PAN_VERIFICATION",
    "costPerRequest": 1.25,
    "timeoutMs": 2500,
    "rateLimitPerMinute": 100,
    "priority": 2,
    "weight": 50,
    "supportedFeatures": ["name_match"]
  }'
```

### 2. List all vendors

```bash
curl http://localhost:3000/vendors
```

### 3. List vendors for specific capability

```bash
curl "http://localhost:3000/vendors?capability=PAN_VERIFICATION"
```

### 4. Set Routing Configuration

```bash
curl -X POST http://localhost:3000/routing-config \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "PAN_VERIFICATION",
    "strategy": "lowest-latency",
    "latencyThresholdMs": 2000,
    "errorRateThreshold": 50
  }'
```

### 5. Get Routing Configurations

```bash
curl http://localhost:3000/routing-config
```

### 6. Route a Request (The Main Event)

```bash
curl -X POST http://localhost:3000/route \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "PAN_VERIFICATION",
    "payload": {
      "pan_number": "ABCDE1234F",
      "name": "Jane Doe"
    },
    "requiredFeatures": ["name_match"]
  }'
```

*Note: Run this command multiple times to see different latencies and strategies in action.*

### 7. View Vendor Metrics

```bash
curl http://localhost:3000/vendor-metrics
```

### 8. View specific vendor metrics

```bash
curl "http://localhost:3000/vendor-metrics?vendor=VendorA"
```

### 9. View Routing Decision Logs

```bash
curl http://localhost:3000/routing-logs
```

### 10. Check System Health

```bash
curl http://localhost:3000/health
```
