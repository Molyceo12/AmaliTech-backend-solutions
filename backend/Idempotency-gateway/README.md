# Idempotency-Gateway (The "Pay-Once" Protocol)

A high-performance payment processing backend with strict idempotency protection and rate-limiting, built with Django REST Framework and Redis.

## 1. Architecture Diagram
![Architecture Flowchart](./assets/flowchart.drawio.svg)
> *This diagram outlines the strict idempotency validation and atomic Redis locking process executed sequentially for every incoming payment request.*

## 2. Prerequisites
Before running the application, ensure you have the following installed on your machine. *(Note: Docker is a system-level application and cannot be installed via `requirements.txt`)*.

- **[Python 3.10+](https://www.python.org/downloads/)**: Required to run the Django API.
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**: Highly recommended. The `Makefile` uses Docker to instantly spin up a secure Redis Cache.
  - *Alternative:* If you absolutely cannot install Docker, you must install Redis locally and start it manually:
    - **Linux**: `sudo apt install redis-server && sudo systemctl start redis-server`
    - **Mac**: `brew install redis && brew services start redis`
    - **Windows**: Install using [Memurai](https://www.memurai.com/) (a Windows-native Redis port) or install via [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install).

## 3. Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Molyceo12/AmaliTech-DEG-Project-based-challenges-solutions.git
   ```

2. **Navigate to the backend project folder**
   ```bash
   cd AmaliTech-DEG-Project-based-challenges-solutions/backend/Idempotency-gateway
   ```

3. **Start the application using the Makefile**
   ```bash
   make start
   ```
   
   **What this single command automatically does for you:**
   - Starts a Redis instance in the background using Docker.
   - Creates a virtual environment and **Installs requirements**.
   - Runs the SQLite database **Migrations**.
   - **Runs the backend server** natively.

*(Note: This requires you to have Docker installed to run the Redis cache, and Python3 to run the web server).*

The API will instantly be available at `http://127.0.0.1:8000/`.

## 4. Production Deployment (Render)
This repository is pre-configured for free deployment on [Render](https://render.com/).
1. Create a new **Web Service** on Render and link this repository.
2. Under **Root Directory**, type `backend/Idempotency-gateway`.
3. Set the **Build Command** to `./build.sh`.
4. Set the **Start Command** to `gunicorn idempotency_gateway.wsgi:application`.
5. Under Environment Variables, add `REDIS_URL` containing your managed Redis connection string.

## 5. API Documentation

### 1. Register API
**Description**: Register a new client/user account to receive starting funds (10000 default balance).
- **URL**: `http://127.0.0.1:8000/api/auth/register/` (Local) OR `https://amalitech-backend-solutions.onrender.com/api/auth/register/` (Live)
- **Method**: `POST`
- **Headers**: 
  - `Content-Type: application/json`
- **Request Body**:
  ```json
  {
      "email": "testuser@domain.com",
      "password": "strongpassword123"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
      "success": true,
      "message": "User registered successfully",
      "data": {
          "email": "testuser@domain.com"
      }
  }
  ```

### 2. Login API
**Description**: Authenticate and retrieve a JWT Access Token.
- **URL**: `http://127.0.0.1:8000/api/auth/login/` (Local) OR `https://amalitech-backend-solutions.onrender.com/api/auth/login/` (Live)
- **Method**: `POST`
- **Headers**: 
  - `Content-Type: application/json`
- **Request Body**:
  ```json
  {
      "email": "testuser@domain.com",
      "password": "strongpassword123"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
      "success": true,
      "message": "Login successful",
      "data": {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5c...",
          "access": "eyJhbGciOiJIUzI1NiIsInR5c..."
      }
  }
  ```

### 3. Process Payment API
**Description**: Process a payment utilizing strict idempotency cache validation and payload hashing.
- **URL**: `http://127.0.0.1:8000/api/auth/process-payment/` (Local) OR `https://amalitech-backend-solutions.onrender.com/api/auth/process-payment/` (Live)
- **Method**: `POST`
- **Headers**: 
  - `Content-Type: application/json`
  - `Idempotency-Key`: `id123` *(Example: any unique identifier or UUID)*
  - `Authorization`: `Bearer <YOUR_ACCESS_TOKEN_HERE>`
- **Request Body**:
  ```json
  {
      "amount": 100.00,
      "currency": "GHS"
  }
  ```
- **Initial Response (201 Created)** *(Executes with 2-second delay)*:
  ```json
  {
      "success": true,
      "message": "Charged 100.0 GHS",
      "data": {
          "transaction_id": "txn_1714200000",
          "amount": 100.0,
          "currency": "GHS",
          "remaining_balance": 9900.0
      }
  }
  ```
- **Duplicate Request Response (Idempotent Hit)** *(Executes instantly without delay)*:
  Returns the exact same JSON response block as above, but with a special response header appended by the server:
  - `X-Cache-Hit: true`

#### **Edge Cases & Error Responses**
- **Token Expired / Missing Token (401 Unauthorized)**:
  ```json
  {
      "success": false,
      "message": "Invalid or expired token"
  }
  ```
- **Missing Idempotency-Key (400 Bad Request)**:
  ```json
  {
      "success": false,
      "message": "Idempotency-Key header is required"
  }
  ```
- **Payload Tampering / Hash Mismatch (409 Conflict)** *(Using an existing key for a different payment amount)*:
  ```json
  {
      "success": false,
      "message": "Idempotency key already used for a different request body."
  }
  ```
- **Rate Limit Exceeded (429 Too Many Requests)** *(More than 5 requests in 10 seconds)*:
  ```json
  {
      "error": "Too many requests"
  }
  ```
- **Insufficient Funds (400 Bad Request)**:
  ```json
  {
      "success": false,
      "message": "Insufficient balance",
      "current_balance": 50.0
  }
  ```

## 6. Design Decisions

### 1. Backend Framework (Django REST Framework)
- **Why**: DRF provides rapid API development with rigorous built-in serialization and validation layers.
- **Justification**: It aligns perfectly with a fintech environment needing strict data consistency. The robust middleware ecosystem seamlessly handles custom JWT authentication (`djangorestframework-simplejwt`), allowing the core engineering focus to remain on complex idempotency logic rather than reinventing underlying security routing.

### 2. Idempotency Storage (Redis)
- **Why**: Idempotency checks happen on *every* payment request and require extreme low-latency processing.
- **Justification**: Redis was chosen over a relational DB for its single-threaded atomic operations and memory-speed read/writes. By utilizing Redis for caching responses and managing TTL (Time-To-Live), the system inherently prunes expired transaction keys without needing scheduled chron jobs, preventing state-table bloat.

### 3. Containerization (Docker)
- **Why**: Financial infrastructure demands absolute environment parity across local, testing, and production servers.
- **Justification**: Wrapping Redis in a Docker container (invoked via the unified `Makefile`) guarantees that any developer or CI pipeline can instantly spin up the required caching layer without fighting system-level dependencies. It completely eliminates the "it works on my machine" anti-pattern.

### 4. Database Choice (SQLite)
- **Why**: Chosen strictly for prototype velocity and portability in this specific repository.
- **Justification**: SQLite allows reviewers to clone, migrate, and run the project with zero external database configuration. While a true production environment would hot-swap this for PostgreSQL to support concurrent writes and transaction isolation, SQLite safely satisfies the lightweight persistence requirements for User and Balance tracking here.

### 5. Concurrency & Race Condition Handling
- **Why**: Network stutters often cause clients to rapidly fire duplicate requests within milliseconds, triggering parallel execution.
- **Justification**: Relying on DB `UNIQUE` constraints is too slow and prone to race conditions. This system employs strict Atomic Redis Locking (`SET NX`). If Request B arrives while identical Request A is still executing, B is safely blocked (polling Redis). Instead of returning a generic error, it waits and instantly returns the cached response once A completes.



## 7. The Developer's Choice

To push this architecture beyond core requirements, I designed three active defense mechanisms to handle the realities of a production fintech environment:

### 1. The Multi-Tiered Redis Defense
Instead of just using Redis to merely check if a key exists, I expanded its role to protect the entire gateway:
- **Idempotency Storage**: Redis caches the completed transaction responses. This guarantees incredibly small response times without running a database query every time a duplicate request arrives.
- **Race Condition Handling (Atomic Locking)**: By using Redis `SET NX`, parallel requests with the same key instantly trigger a lock. This completely solves the "in-flight" concurrency problem without database deadlocks.
- **Strict Rate Limiting**: The API immediately rejects looping clients (max 5 requests per 10s) with a `429 Too Many Requests` status, defending the server against memory abuse and repetitive attack behavior.
- **Request Integrity Hash**: An idempotency key alone is not secure. If a client tampers with the payment amount but reuses an old key, Redis detects a SHA-256 payload mismatch and securely blocks the transaction with a `409 Conflict`.

### 2. Token-Based Authentication (JWT)
**Why it was added**: Financial gateways cannot safely process anonymous traffic. 
**Detailed Explanation**: I implemented a custom middleware interceptor that mathematically enforces JWT validation. This cryptographically binds an `Idempotency-Key` to a specific user, totally neutralizing attacks where malicious users attempt to hijack or replay keys belonging to different clients.

### 3. Strict Request Validation
**Why it was added**: Gateways must fail fast on malformed inputs before engaging the database logic.
**Detailed Explanation**: The API actively intercepts and validates payloads for strict constraints (e.g., amount must be a positive float; missing fields are caught). This eliminates unhandled parsing errors deep in the transaction pipeline and massively reduces the surface area for injection attacks.
