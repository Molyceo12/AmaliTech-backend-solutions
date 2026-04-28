# Pulse-Check-API (The "Watchdog" Sentinel)

A high-reliability monitoring system that tracks remote device heartbeats and triggers critical alerts when communication falls silent. Built with Django REST Framework, Celery, and Redis for distributed background processing.

## 1. Architecture Diagram
![System Flowchart](pulse_check.drawio.svg)
> *This diagram illustrates the stateful lifecycle of a monitor. The "Watchdog" (Celery) asynchronously tracks heartbeats in Redis and fires a background alert the moment a device misses its communication window.*

## 2. Prerequisites
Ensure you have the following installed to run the sentinel infrastructure:

- **[Python 3.10+](https://www.python.org/downloads/)**: Required to run the Django API and Celery worker.
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**: Used to instantly spin up the Redis message broker.
  - *Alternative:* If you don't have Docker, you must start a Redis server locally on `localhost:6379`.

## 3. Setup Instructions

1. **Clone and Navigate**
   ```bash
   cd AmaliTech-DEG-Project-based-challenges-solutions/backend/Pulse-Check
   ```

2. **Start the Sentinel using the Makefile**
   ```bash
   make start
   ```
   
   **What this command automatically does for you:**
   - Starts a **Redis instance** via Docker (ignore errors if already running).
   - Creates a virtual environment and **Installs requirements**.
   - Runs **Database migrations**.
   - Launches both the **Django API** and the **Celery Sentinel** in a single unified terminal view.

## 4. API Documentation

### 1. Register Monitor
**Description**: Register a new device to the monitoring system.

**Url Localhost**
```bash
curl -X POST http://127.0.0.1:8000/register_monitor
```

**Url Live**
```bash
curl -X POST https://pulse-check-5g1i.onrender.com/register_monitor
```

**Request Body**
```json
{
  "id": "device-01", 
  "timeout": 60, 
  "alert_email": "admin@critmon.com"
}
```

**Response Body**
```json
{
    "id": "device-01",
    "timeout": 60,
    "alert_email": "admin@critmon.com",
    "status": "active",
    "last_heartbeat": null
}
```

### 2. Device Heartbeat (Reset)
**Description**: Reset the watchdog timer for an active device.

**Url Localhost**
```bash
curl -X POST http://127.0.0.1:8000/monitors/device-01/heartbeat
```

**Url Live**
```bash
curl -X POST https://pulse-check-5g1i.onrender.com/monitors/device-01/heartbeat
```

**Response Body**
```json
{
    "success": true,
    "message": "Heartbeat received. Device is active.",
    "id": "device-01"
}
```

### 3. Check Device Status
**Description**: Retrieve the real-time health status of a device.

**Url Localhost**
```bash
curl -X GET http://127.0.0.1:8000/monitors/device-01/status
```

**Url Live**
```bash
curl -X GET https://pulse-check-5g1i.onrender.com/monitors/device-01/status
```

**Response Body**
```json
{
    "id": "device-01",
    "timeout": 60,
    "alert_email": "admin@critmon.com",
    "status": "active",
    "last_heartbeat": "2026-04-27T15:53:42Z"
}
```

### 4. Pause Monitoring (Snooze)
**Description**: Temporarily stop monitoring for maintenance.

**Url Localhost**
```bash
curl -X POST http://127.0.0.1:8000/monitors/device-01/pause
```

**Url Live**
```bash
curl -X POST https://pulse-check-5g1i.onrender.com/monitors/device-01/pause
```

**Response Body**
```json
{
    "success": true, 
    "message": "Monitoring paused for device-01."
}
```

## 5. Design Decisions

### 1. Backend Framework (Django REST Framework)
- **Why**: DRF provides rapid API development with a rigorous built-in serialization and validation layer.
- **Justification**: In a monitoring system, data integrity is paramount. By using DRF, I ensured that every incoming heartbeat and registration request is validated against strict constraints (e.g., positive integers for timeouts) before any background logic is triggered. This creates a "Fail-Fast" architecture that protects the system from malformed data.

### 2. Distributed Task Queue (Celery)
- **Why**: Handling thousands of concurrent countdown timers using native OS threads or memory-mapped objects would rapidly overload the main API process, leading to memory bloat and eventual crashes.
- **Justification**: Celery was chosen to offload the heavy "Watchdog" logic to a separate dedicated worker process. By using a distributed queue, the system ensures that the main API remains responsive and thin, while Celery handles the background timing logic with maximum CPU efficiency and process isolation.

### 3. State Management & Messaging (Redis)
- **Why**: The system requires extreme low-latency for frequent heartbeat resets.
- **Justification**: Redis serves two critical roles: it acts as the high-performance broker for Celery tasks and as a real-time activity cache. By managing heartbeats in Redis instead of performing heavy database writes every second, the system can scale to monitor thousands of devices simultaneously with minimal performance overhead.

### 4. Atomic Task Management
- **Why**: Overlapping timers can lead to "False Positive" alerts if multiple tasks are scheduled for the same device.
- **Justification**: I implemented a strict **Atomic Task ID** system. Each device stores its current active `task_id` in the database. When a new heartbeat arrives, the system uses this ID to `revoke` the previous timer before scheduling a new one. This guarantees that each device has exactly **one** active watchdog at any given time, preventing race conditions.

### 5. Deployment & Parity (Docker)
- **Why**: Monitoring infrastructure must be reproducible across any environment (Testing, QA, Production).
- **Justification**: Utilizing a unified Docker-based workflow ensures that the Redis networking and the Python environment are identical for every user. Any tester can use the `make` utility to spin up the entire infrastructure without fighting local system dependencies.

## 6. The Developer's Choice: Why these choices?

To build a **Fintech-grade** sentinel, I implemented three key safety layers:

### 1. Redis vs. Supabase (PostgreSQL)
In a production environment, heartbeats happen thousands of times per second. Writing to a traditional Database (Supabase/Postgres) for every ping would cause a massive bottleneck.
**The Choice:** We use Redis for tracking because its RAM-based speed allows for sub-millisecond updates, and its **Atomic Locking** prevents race conditions where two heartbeats might accidentally trigger or clear the same alert.

### 2. Celery for Load Management
Instead of running timers inside the Django process (which would hog memory and potentially crash the API), we offload the "Watchdog" work to **Celery**.
**The Choice:** This keeps the system **efficient** and **unburdened**. The worker process handles the countdowns independently, ensuring the API is always free to accept new heartbeats even if thousands of devices are being monitored simultaneously.

### 3. Strict Validation & Real-Time Observer (Status API)
Fintech companies demand absolute observability. You cannot wait for an error to know a system is down.
**The Choice:**
- **Strict Validation**: We block malformed data (like negative timeouts) at the door, preventing corrupted state from ever entering the watchdog queue.
- **Get Status API**: This provides the user with **Immediate Observability**, allowing internal teams to manually verify a device's health without waiting for an automated alert email.
