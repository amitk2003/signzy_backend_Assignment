# Intelligent Vendor Routing Platform

A smart backend system that acts as an intelligent middleman between clients and multiple third-party vendors. It routes requests to the best available vendor based on configurable rules, tracks performance metrics, and automatically handles failovers when things go wrong.

## 🚀 Features

- **5 Routing Strategies**: 
  - Priority-based
  - Weighted (e.g., 70/30 split)
  - Lowest Latency (picks the fastest vendor)
  - Lowest Cost (picks the cheapest vendor)
  - Round-Robin (distributes evenly)
- **Automatic Failover**: If a vendor times out, errors out, or rate-limits you, the system automatically tries the next best vendor.
- **Health Tracking**: Vendors are marked as unhealthy if their error rate exceeds 50% or they have 5 consecutive failures.
- **Rate Limiting**: Per-vendor rate limits (sliding window) prevent you from exceeding your quotas.
- **Simulated Vendors**: Includes a built-in simulator that generates realistic latencies, occasional failures, and timeouts so you can see failover working in real-time.

## 🛠️ Tech Stack

- **Python 3.14**
- **Flask 3.1.3**
- **In-Memory Storage**: No external database required. Data is stored in memory for easy setup and testing.

## 📦 Getting Started

### 1. Install Requirements
Make sure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python app.py
```
The server will start on `http://localhost:3000`. 
*Note: Sample vendors and routing configurations are automatically loaded on startup!*

## 📖 API Documentation

### 1. Register a Vendor
Add a new vendor or update an existing one.

**POST `/vendors`**
```json
{
  "name": "VendorA",
  "capability": "PAN_VERIFICATION",
  "costPerRequest": 1.5,
  "timeoutMs": 2000,
  "rateLimitPerMinute": 100,
  "priority": 1,
  "weight": 70,
  "supportedFeatures": ["name_match"]
}
```

### 2. Route a Request (Main Endpoint)
Send a request to be routed to the best vendor. The client does not need to know which vendor is used.

**POST `/route`**
```json
{
  "capability": "PAN_VERIFICATION",
  "payload": {
    "pan_number": "ABCDE1234F"
  },
  "requiredFeatures": ["name_match"]
}
```

**Response:**
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "capability": "PAN_VERIFICATION",
    "vendor_used": "VendorA",
    "strategy": "weighted",
    "latency_ms": 142,
    "skipped_vendors": [],
    "failover_chain": [
      {
        "vendor": "VendorA",
        "status": "SUCCESS",
        "latency_ms": 142
      }
    ]
  }
}
```

### 3. Configure Routing Rules
Change how the system picks vendors for a capability.

**POST `/routing-config`**
```json
{
  "capability": "PAN_VERIFICATION",
  "strategy": "lowest-latency",
  "latencyThresholdMs": 1500
}
```

### 4. System Observability
- **GET `/vendors`**: List all registered vendors
- **GET `/vendor-metrics`**: See success/error rates, avg latency, and health status for all vendors
- **GET `/routing-logs`**: See the history of routing decisions, failovers, and reasons for skipping vendors
- **GET `/health`**: Check overall system health

## 🧪 Testing

A comprehensive smoke test is included that verifies all endpoints, edge cases, and failover logic.

```bash
python test/smoke_test.py
```

## 🧠 Design Decisions & Edge Cases Handled

- **In-Memory Storage with Thread Locks**: Ensures thread safety when handling concurrent requests without needing an external database.
- **Zero-Latency Fallback**: If a vendor has no metrics yet (e.g., just registered), the `lowest-latency` strategy treats its latency as `0` to give it a chance to be used and build metrics.
- **Failover Chain Logging**: Every request returns a `failover_chain` in the metadata, detailing exactly which vendors were tried and why they failed, providing full transparency.
- **Smart Capability Filtering**: All capabilities are normalized to uppercase and stripped of whitespace to prevent mismatch errors.
