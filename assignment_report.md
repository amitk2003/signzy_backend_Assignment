# Vendor Routing Platform - Project Report

## Introduction
This report outlines the technical decisions and features I built for the Intelligent Vendor Routing Platform. My goal was to create a robust middleman between clients and third-party vendors that can handle routing, tracking, and failovers smoothly.

## Technical Decisions

### Why an In-Memory Database?
For this assignment, I decided to use an in-memory database (using standard Python dictionaries and lists) instead of a traditional database like PostgreSQL or MongoDB. 

Here is why I took this approach:
- **No Setup Required**: I wanted the project to be easy to run. Anyone can just clone the repo and start the server without setting up databases or Docker containers.
- **Focus on the Core Problem**: The assignment is mostly about routing logic and failovers. Dealing with database schemas and connections would add unnecessary overhead.
- **Speed**: Since routing decisions need to be fast (checking metrics and configs on the fly), keeping the data in memory eliminates network latency entirely.
- **Thread Safety**: To make sure the system handles concurrent requests properly, I used Python's `threading.Lock()` to keep metrics and rate limits accurate under load.

Since this is a prototype and data persistence across server restarts wasn't strictly required, the in-memory approach was the most practical choice.

### Use of AI Assistants
I built this project myself, but I did use AI coding assistants to speed up my workflow. I used them mainly as a pair-programmer to help generate boilerplate code, format documentation, and quickly catch syntax errors. However, all the core architectural decisions, routing algorithms, and system design choices were entirely mine.

## System Features

### 1. Automatic Failover
If the system tries to route a request to a vendor and that vendor times out, throws an error, or hits a rate limit, the request doesn't just fail. The system temporarily skips that vendor and tries the next best option based on the active routing rules. The client only sees an error if every single available vendor fails.

### 2. Vendor Health Tracking
I added a system to track how well vendors are performing in real-time. Every API call is logged as a success or failure. If a vendor's error rate goes above 50%, or if it fails 5 times in a row, the system marks it as "unhealthy." Unhealthy vendors are automatically skipped so we don't waste time trying to call a broken service.

### 3. Rate Limiting
To respect vendor API limits, I implemented a sliding window rate limiter. The system checks how many requests a vendor has handled in the last minute. If it's getting close to its `rateLimitPerMinute` limit, the system gracefully shifts traffic to other vendors to prevent HTTP 429 (Too Many Requests) errors.

### 4. Metrics & Logging (Observability)
I built out endpoints to make it easy to see what the system is doing:
- `/vendor-metrics`: Shows real-time stats for each vendor, like total requests, success rates, and average response times.
- `/routing-logs`: Shows exactly why the system made a routing decision. It includes which vendor was picked, what strategy was used, which vendors were skipped and why, and the full failover chain.

### 5. Routing Strategies
The core of the engine relies on 8 distinct routing strategies, designed using a clean Strategy Pattern so they can be swapped instantly via the configuration API. The system currently supports:

- **Priority-Based Routing**: Ranks vendors by a static priority number. Lower numbers mean higher priority (e.g., Priority 1 is checked before Priority 2).
- **Weighted Routing**: Distributes traffic proportionally across vendors based on a percentage weight, which is useful for A/B testing or gradual rollouts (e.g., sending 70% of traffic to Vendor A and 30% to Vendor B).
- **Lowest Latency Routing**: Dynamically checks the historical average response time of available vendors and routes the request to the fastest one.
- **Lowest Cost Routing**: Optimizes for budget by always picking the vendor with the lowest `costPerRequest`.
- **Round-Robin Routing**: Cycles through all available vendors evenly in sequential order to distribute the load perfectly across the board.
- **Health-Based Routing**: Focuses on reliability by dynamically routing to the vendor with the highest historical success rate, avoiding vendors that are throwing occasional errors.
- **Feature-Based Routing**: Selects the vendor that supports the highest number of overall features, which is useful when a complex request requires a highly versatile vendor.
- **Strict Failover Routing**: Operates as a strict fallback sequence. It relies heavily on an explicit priority chain, automatically cascading down the list the moment the primary vendor drops a request or times out.

## Challenges Faced

While building this platform, I encountered a few interesting technical challenges that required careful design:

1. **Handling Concurrent Data Access**: 
   Since I opted for an in-memory data store, I quickly realized that concurrent incoming API requests could cause race conditions. If two requests tried to update a vendor's success rate or rate-limit counter at the exact same millisecond, data could be lost or corrupted. I solved this by wrapping all write operations in the `DataStore` with Python's `threading.Lock()`, ensuring thread-safe operations without sacrificing much speed.

2. **Preventing Infinite Failover Loops**: 
   When designing the automatic failover system, there was a risk that the system might get stuck in a loop repeatedly trying to call the same failing vendors, especially in strategies like Round-Robin. I handled this by passing a `tried_vendors` set through the failover loop, ensuring that a vendor is strictly removed from the candidate pool once it fails during a single request lifecycle.

3. **The "Cold Start" Problem for Latency Routing**: 
   When evaluating the `Lowest Latency` strategy, a brand new vendor has no historical latency data. If the system defaults to ignoring it, a new vendor would never be picked. I solved this by treating a lack of metrics as "0 latency." This guarantees that newly registered vendors get prioritized immediately to build up their initial performance metrics.

## API Documentation
I have also provided full API documentation using OpenAPI (Swagger). You can find the `swagger.yaml` file in the project root, which details all endpoints, request bodies, and responses.
