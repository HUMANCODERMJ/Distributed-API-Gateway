# Redis Architecture and Systems Design

This document provides a deep-dive analysis of Redis architecture, persistence models, and its role in high-throughput systems, specifically tailored for Computer Science students and Backend Engineers.

---

## 1. The Core Execution Engine: Single-Threaded Event Loop

Redis is famous for its performance despite being single-threaded. This is achieved through the **Reactor Pattern**.

### Concepts and Relativity

- **The Single-Threaded Model:** Redis executes all data-modifying commands on a single main thread. This eliminates the need for locks (mutexes) and prevents expensive CPU context switching.
- **The Event Loop:** The mechanism that orchestrates synchronous execution and asynchronous I/O.
  - **Call Stack (LIFO):** Where your Redis commands (like `GET`, `SET`) are executed synchronously.
  - **I/O Multiplexing (epoll/kqueue):** The thread doesn't "wait" for a network packet. It asks the OS Kernel to notify it only when data is ready on a socket.
  - **Queues (FIFO):** Once the Kernel completes a task, the callback is placed in a queue. The Event Loop pushes these back to the Call Stack only when the stack is empty.

### Performance Impact

Because Redis is *in-memory*, the CPU never stalls waiting for a disk seek. The bottleneck is usually the network bandwidth or memory speed, not the single thread itself.

---

## 2. The Key-Value Storage Model

Redis treats data as an opaque collection of unique identifiers (**keys**) and data structures (**values**).

- **Big-O Complexity:**
  - `GET` / `SET`: *O(1)* constant time lookup via internal hash tables.
  - `LPUSH` / `RPOP`: *O(1)* for linked list operations.
  - `KEYS *`: *O(N)* - The "Stop-the-World" command. Since there is only one thread, an *O(N)* scan blocks all other clients until completion.
- **Memory vs. Disk:** RAM access is ~1,000× faster than SSD access. Redis leverages this "latency gap" to achieve millions of operations per second.

---

## 3. Persistence: Bridging RAM and Disk

To solve the volatility of RAM, Redis uses two primary persistence methods.

### A. RDB (Redis Database Backup)

- **Mechanism:** A point-in-time binary snapshot (`dump.rdb`).
- **Pros:** Extremely fast to load during a restart; compact file size.
- **Cons:** High risk of data loss. If the server crashes between snapshots, all data since the last "save" is lost.

### B. AOF (Append Only File)

- **Mechanism:** A continuous log of write commands (`appendonly.aof`).

#### The Role of `fsync`

When Redis writes to AOF, the data first hits the OS Page Cache (RAM). `fsync` is the system call that forces the OS to physically write those bits to the disk hardware.

- **Policies:**
  - `always` (maximum safety, slow)
  - `everysec` (1s data loss risk, fast)
  - `no` (OS decides, maximum speed)

- **Priority:** On restart, Redis always loads AOF first because it is more likely to be up-to-date than an RDB snapshot.

---

## 4. Memory Management and Expiration

### Maxmemory and Eviction

- **Configured limit:** 8 GB (`8,589,934,592` bytes).
- **Policy:** `noeviction` — when 8 GB is reached, Redis returns an error for all new writes.
- **Alternative:** `allkeys-lru` — automatically deletes Least Recently Used keys to make room.

### Expiration Logic

- **Lazy Expiration:** A key is only deleted when a user tries to access it and Redis realizes it's expired.
- **Active Expiration:** Redis runs a background cycle 10 times per second to randomly sample keys and delete expired ones.

> **Critical Note:** In a high-throughput system, without Active Expiration, memory would fill with "zombie" keys that are never accessed again, causing a memory leak.

---

## 5. High-Throughput Rate Limiters

A rate limiter is a gatekeeper for APIs. "High-throughput" refers to the ability to handle millions of checks per second.

### Why Redis?

- **Atomic Increments:** Commands like `INCR` happen in a single step, preventing race conditions.
- **TTL (Time-To-Live):** Using `SETEX`, you can create a counter that automatically disappears after a window (e.g., 60 seconds).
- **Distributed State:** Since all your API servers talk to the same Redis instance, the rate limit is enforced globally across your entire infrastructure.

---

## 6. CLI Quick Reference (PowerShell & CMD)

### Batch Key Creation (5 s TTL)

**PowerShell:**
```powershell
1..1000 | ForEach-Object { redis-cli SETEX "key_$_" 5 "value_$_" }
```

**CMD (Command Prompt):**
```cmd
FOR /L %i IN (1,1,1000) DO redis-cli SETEX key_%i 5 value_%i
```

### Server Inspection

- `INFO persistence`: Check the status of AOF and RDB.
- `CONFIG GET maxmemory`: Verify the 8 GB limit.
- `MONITOR`: Watch the event loop process commands in real‑time.
