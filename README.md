# Redis Architecture and Systems Design

# 1. What Redis Actually Is

Redis is best described as:

> **An in‑memory data structure server with optional persistence.**

Unlike traditional relational databases such as PostgreSQL or MySQL, Redis does not primarily operate around tables and rows.

Instead it exposes **native data structures** that can be manipulated directly.

These include:

* Strings
* Lists
* Sets
* Hashes
* Sorted Sets (ZSET)
* Streams
* Bitmaps
* HyperLogLogs

This design allows Redis to perform complex operations **directly inside the server** rather than transferring raw data to the application.

Example:

Instead of:

Application → fetch data → modify → send back

Redis allows:

Application → send command → Redis modifies data atomically

This greatly reduces network overhead and improves performance.

---

# 2. Why Redis Is Extremely Fast

Redis performance is the result of several architectural decisions working together.

## 2.1 In‑Memory Storage

The entire working dataset is stored in **RAM**.

Latency comparison:

| Storage   | Typical Latency |
| --------- | --------------- |
| CPU cache | ~1 ns           |
| RAM       | ~100 ns         |
| SSD       | ~100 μs         |
| HDD       | ~10 ms          |

RAM access is **thousands to millions of times faster than disk access**.

Because Redis performs operations in memory, it avoids disk I/O during normal operation.

---

## 2.2 Single‑Threaded Command Execution

Redis executes commands on a **single main thread**.

Benefits:

* No locks
* No mutex contention
* No race conditions inside the core
* No context switching overhead
* Deterministic execution order

Every command is processed sequentially.

This means:

```
Client A → INCR counter
Client B → INCR counter
```

Execution order is guaranteed.

The counter will always be incremented twice without corruption.

This gives Redis **built‑in atomicity for single commands**.

---

## 2.3 Event Loop and Reactor Pattern

Redis uses an **event‑driven architecture**.

The main thread runs an **event loop** which continuously processes:

1. Network events
2. Client commands
3. Background tasks

The design follows the **Reactor Pattern**.

### Key Components

**Call Stack (LIFO)**

Commands such as:

```
GET key
SET key value
```

are executed synchronously on the stack.

**I/O Multiplexing**

Redis uses OS mechanisms such as:

* epoll (Linux)
* kqueue (BSD/macOS)

Instead of waiting for each client connection individually, Redis asks the kernel:

> "Notify me only when a socket is ready to read or write."

This allows thousands of connections to be handled efficiently by a single thread.

**Event Queue**

Once the kernel detects a ready socket, the event is pushed into a queue and processed by Redis.

---

## 2.4 CPU Cache Efficiency

Because Redis runs on a single thread:

* Memory access patterns are predictable
* CPU cache locality is preserved
* Cache‑line bouncing between cores is avoided

This dramatically improves L1/L2 cache efficiency.

---

## 2.5 Efficient Internal Data Structures

Redis uses highly optimized structures internally:

* Hash tables
* Skip lists (used in Sorted Sets)
* Compact encodings
* SDS (Simple Dynamic Strings)

Most operations are:

* **O(1)** constant time
* **O(log n)** logarithmic time

This predictable complexity enables extremely high throughput.

---

# 3. The Single‑Threaded Event Loop Model

Redis's core execution model revolves around a **single‑threaded event loop**.

### Workflow

1. Clients send commands via TCP sockets
2. OS kernel detects socket readiness
3. Event loop processes the command
4. Redis executes command in memory
5. Response returned to client

Because commands execute sequentially, Redis guarantees:

* Atomic command execution
* Deterministic behavior

### Head‑of‑Line Blocking

The downside of this model is that **long‑running commands block all clients**.

Examples of dangerous commands:

* `KEYS *`
* Large Lua scripts
* Huge multi‑key operations

If a command takes 2 seconds, **all clients wait 2 seconds**.

---

# 4. Key‑Value Storage Model

Redis stores data as:

```
Key → Value
```

Keys are unique identifiers.

Values are Redis data structures.

Example:

```
user:1001 → {name: "Alice", age: 30}
```

### Complexity Examples

| Command | Complexity |
| ------- | ---------- |
| GET     | O(1)       |
| SET     | O(1)       |
| LPUSH   | O(1)       |
| HSET    | O(1)       |
| ZADD    | O(log n)   |
| KEYS *  | O(N)       |

`KEYS *` scans the entire dataset and blocks Redis.

In production systems, `SCAN` is used instead.

---

# 5. Persistence: Bridging RAM and Disk

RAM is volatile.

To prevent total data loss, Redis offers persistence mechanisms.

---

## 5.1 RDB (Redis Database Snapshot)

RDB creates **point‑in‑time snapshots** of the dataset.

Stored as:

```
dump.rdb
```

### Mechanism

Redis forks a child process.

The child process writes the snapshot to disk while the parent continues serving clients.

### Advantages

* Compact file
* Fast restart
* Minimal runtime overhead

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
