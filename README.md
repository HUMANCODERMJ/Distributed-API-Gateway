"""
Distributed API Gateway - Phase 1

A lightweight, modular reverse proxy gateway built with FastAPI that forwards requests to downstream services with rate limiting and request logging.

## Architecture Overview

```
Client Request
    ↓
[Gateway - Port 8000]
    ├─ Request Logger Middleware
    ├─ Rate Limiting (Redis)
    ├─ Route Matching
    ├─ Request Forwarding
    └─ Response Return
    ↓
[Downstream Services]
    ├─ User Service (Port 8001)
    ├─ Order Service (Port 8002)
    └─ AI Service (Port 8003)
```

## Project Structure

```
app/
├── core/              # Configuration and logging setup
│   ├── config.py      # Centralized configuration (routes, Redis, timeouts)
│   └── logging_config.py  # Logging setup
├── routes/            # HTTP route handlers
│   └── proxy.py       # Catch-all proxy endpoint with rate limiting
├── services/          # Business logic layer
│   ├── proxy_service.py   # Request forwarding logic
│   └── redis_service.py   # Redis operations (rate limiting)
├── middleware/        # HTTP middleware
│   └── request_logger.py  # Request/response logging
├── utils/             # Utilities
│   └── helpers.py     # Helper functions
└── main.py            # FastAPI app entry point

downstream_services/  # Test/dummy downstream services
├── user_service/      # Port 8001
├── order_service/     # Port 8002
└── ai_service/        # Port 8003
```

## Features

✅ **Request Forwarding** - Forwards HTTP requests to downstream services preserving method, headers, query params, and body
✅ **Route Matching** - Path-prefix based route matching configuration in `app/core/config.py`
✅ **Rate Limiting** - Redis-backed rate limiting with atomic Lua scripts
✅ **Request Logging** - Middleware logs incoming requests and response status/timing
✅ **Health Checks** - `/health` and `/readiness` endpoints for monitoring
✅ **Error Handling** - Proper error responses for routing failures and downstream errors
✅ **Async Throughout** - All operations are fully async using httpx and aioredis

## Setup and Running

### Prerequisites

- Python 3.8+
- Redis server running on localhost:6379
- Virtual environment (recommended)

### Installation

1. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Gateway

Start the main gateway:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or using the entry point:

```bash
python app/main.py
```

### Running Downstream Services

Start each downstream service in separate terminals:

```bash
# Terminal 1 - User Service (Port 8001)
python downstream_services/user_service/main.py

# Terminal 2 - Order Service (Port 8002)
python downstream_services/order_service/main.py

# Terminal 3 - AI Service (Port 8003)
python downstream_services/ai_service/main.py
```

## Testing the Gateway

### Check Gateway Health

```bash
curl http://localhost:8000/health
# Response: {"status": "healthy"}
```

### Test User Service Routing

```bash
# List all users
curl http://localhost:8000/users

# Get specific user
curl http://localhost:8000/users/1
```

### Test Order Service Routing

```bash
# List all orders
curl http://localhost:8000/orders

# Get specific order
curl http://localhost:8000/orders/101
```

### Test AI Service Routing

```bash
# Test endpoint
curl http://localhost:8000/ai/test

# Chat endpoint (requires JSON body)
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}'
```

### Test Rate Limiting

Make 11+ requests within 60 seconds to trigger the 10-request limit:

```bash
for i in {1..15}; do curl http://localhost:8000/users; done
# After 10 requests, you'll get: {"error": "Rate limit exceeded"}
```

## Configuration

Edit `app/core/config.py` to modify:

- **Routes**: Add/remove downstream service mappings
- **Redis Settings**: Change host, port, database
- **Rate Limiting**: Adjust request limits and time windows
- **HTTP Client**: Modify timeouts and connection pool size
- **Logging Level**: Set DEBUG, INFO, WARNING, ERROR

Example:

```python
ROUTES = {
    "/users": "http://localhost:8001",
    "/orders": "http://localhost:8002",
    "/ai": "http://localhost:8003",
    "/payments": "http://payment-service:8004",  # Add new service
}
```

## Request Flow

1. **Incoming Request** → Gateway (port 8000)
2. **Request Logger Middleware** → Logs method, path, client
3. **Rate Limit Check** → Redis counter atomically incremented
   - If exceeded (>10 in 60s) → 429 response
   - If allowed → Continue
4. **Route Matching** → Path prefix matched to downstream URL
   - If no match → 404 response
   - If match → Continue
5. **Request Forwarding** → httpx forwards to downstream service
   - Preserves method, headers, query params, body
6. **Response Return** → Downstream response returned as-is
   - Status code, headers, content preserved

## Known Limitations (Phase 1)

- No request/response caching
- No retry logic for failed requests
- No load balancing across multiple instances
- No circuit breaker pattern
- No request authentication/authorization
- No request/response transformation
- Routing is simple prefix matching only

These will be addressed in future phases.

## Architecture Decisions

### Why httpx over requests?

- Async/await support out of the box
- Connection pooling
- Better for high-throughput gateway scenarios

### Why Lua scripts for rate limiting?

- Atomic operations without race conditions
- Single round-trip to Redis
- Window-based counters with automatic expiration

### Why middleware over route decorators?

- Applies to all routes uniformly
- Easier to add/remove global behaviors
- Better separation of concerns

### Why service classes over functions?

- Centralized resource management (client lifecycle)
- Reusable across routes
- Easier testing and mocking

## Future Extensions (Phase 2+)

- [ ] Request caching with Redis
- [ ] Retry logic with exponential backoff
- [ ] Load balancing (round-robin, least connections)
- [ ] Circuit breaker pattern
- [ ] Request/response compression
- [ ] Authentication (API keys, JWT)
- [ ] Request transformation/sanitization
- [ ] Metrics collection (Prometheus)
- [ ] Distributed tracing (OpenTelemetry)
- [ ] GraphQL gateway support

### Disadvantages

* Possible data loss between snapshots
* Fork operation may temporarily increase memory usage

---

## 5.2 AOF (Append Only File)

AOF logs **every write command**.

Example:

```
SET user:1 "Alice"
INCR page_views
```

On restart Redis **replays commands** to rebuild state.

### Advantages

* Higher durability
* Smaller data loss window

### Disadvantages

* Larger file size
* Slower restart time

---

## 5.3 Fsync Policies

When writing AOF entries, Redis must ensure data reaches disk.

`fsync` forces the OS to flush buffers to disk hardware.

Policies:

```
appendfsync always
appendfsync everysec
appendfsync no
```

### Tradeoff

| Policy   | Safety   | Performance |
| -------- | -------- | ----------- |
| always   | highest  | slow        |
| everysec | balanced | fast        |
| no       | lowest   | fastest     |

Most production systems use **everysec**.

---

# 6. Restart Behavior

If both AOF and RDB exist:

Redis loads **AOF first**.

Reason:

AOF contains more recent operations than the snapshot.

If AOF is disabled, Redis loads `dump.rdb`.

---

# 7. Memory Model

Redis keeps the **entire active dataset in RAM**.

Disk is used only for persistence.

This differs from traditional databases.

Example comparison:

| Feature         | Redis            | MySQL           |
| --------------- | ---------------- | --------------- |
| Primary storage | RAM              | Disk            |
| RAM role        | main dataset     | cache buffer    |
| Disk access     | persistence only | primary storage |

MySQL loads pages from disk on demand.

Redis does **not page data from disk dynamically**.

---

# 8. Memory Limits and Eviction Policies

Redis memory usage can be limited using:

```
maxmemory
```

Example:

```
maxmemory 8gb
```

If memory limit is reached:

### noeviction

Redis rejects writes.

Error:

```
OOM command not allowed
```

### LRU / LFU policies

Redis evicts keys automatically.

Common policies:

* allkeys-lru
* volatile-lru
* allkeys-lfu
* volatile-ttl

These are useful when Redis acts as a **cache layer**.

---

# 9. Expiration Mechanisms

Redis supports TTL‑based expiration.

Example:

```
SET session "abc"
EXPIRE session 60
```

But expiration is **not instantaneous deletion**.

Redis uses two strategies.

---

## 9.1 Lazy Expiration

When a client accesses a key:

Redis checks if TTL has expired.

If expired:

* key is deleted
* nil returned

This means expired keys may remain in memory until accessed.

---

## 9.2 Active Expiration

Redis periodically samples keys with TTL.

Frequency:

~10 times per second.

It deletes expired keys probabilistically.

Without active expiration, unused expired keys would accumulate in memory.

---

# 10. Atomicity and Race Conditions

Because Redis executes commands sequentially:

Each command is **atomic**.

Example:

```
INCR counter
```

No two commands run simultaneously.

However race conditions can occur if multiple commands are used.

Example:

```
GET counter
SET counter counter+1
```

Solution:

* Lua scripts
* MULTI/EXEC transactions

---

# 11. Performance Discipline

Because Redis has a single execution thread, poor commands affect everyone.

Avoid:

* `KEYS *`
* large Lua loops
* large blocking operations

Use instead:

* `SCAN`
* pipelining
* small atomic commands

---

# 12. High‑Throughput Rate Limiting with Redis

Redis is ideal for distributed rate limiters.

Reasons:

* Atomic increments
* Fast TTL expiration
* Shared state across servers

Example approach:

```
INCR user:123
EXPIRE user:123 60
```

Each API request increments a counter.

If counter exceeds limit → reject request.

Redis ensures the increment is atomic.

---

# 13. CLI Tools for Inspection

Useful commands:

```
INFO memory
INFO persistence
CONFIG GET maxmemory
MONITOR
DBSIZE
```

These allow engineers to inspect server state and behavior.

---
