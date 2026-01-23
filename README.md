# ShopStream

A **production-grade, event-driven e-commerce backend** built with **FastAPI**, **PostgreSQL**, **Redis Streams**, **Celery**, and **Docker**.  
It demonstrates **distributed systems fundamentals**, **saga orchestration**, **outbox pattern**, **background workers**, **dead-letter handling**, and a **safe agentic AI assistant (ShopAgent)**.

ShopStream is designed as a **senior-level backend portfolio project**, optimized for **interview explanation, debugging, and architectural clarity**, not UI polish.

---

## 📁 Repository

GitHub: https://github.com/harshdoshi2711/ShopStream.git

---

## ✨ Features

### 🔹 Core E-Commerce Flow
- Product catalog with inventory
- Order creation with transactional outbox
- Inventory reservation & release
- Simulated payments (success & failure)
- Event-driven order lifecycle
- Choreography-based saga (no central orchestrator)

### 🔹 Event-Driven Architecture
- **Redis Streams** as the event bus
- Consumer groups per service
- At-least-once delivery
- Idempotent consumers with processed-event ledgers
- Clear separation between commands & events

### 🔹 Saga & Failure Handling
- Inventory failure → order cancellation
- Payment failure → inventory compensation
- Fully asynchronous flow
- Business-level saga timeline visualization (clean, deduplicated)

### 🔹 Outbox Pattern
- Orders persist events in the same DB transaction
- Background worker publishes events reliably
- Prevents lost events during crashes

### 🔹 Background Workers
- Celery workers for:
  - Outbox publishing
  - Dead-letter retries
- Redis-backed task queue
- Exponential retry with max attempts

### 🔹 Dead-Letter Queue (DLQ)
- Failed events pushed to a DLQ stream
- Periodic scanning via Celery Beat
- Safe replay with retry count tracking

---

## 🤖 ShopAgent (Agentic AI)

**ShopAgent** is a user-facing AI assistant integrated safely into the system.

### Capabilities
- Show trending products
- Filter products by category & price
- Explain why an order succeeded or failed
- Identify the saga step that caused failure
- Suggest alternatives for out-of-stock products

### Safety & Constraints
- Read-only access
- No state mutation
- No order or inventory creation
- LLM used **only** for intent classification
- All data access via deterministic backend tools
- Graceful fallback on AI failure

---

## 🖥️ Minimal Debug UI

A **plain server-rendered UI** built with Jinja2, hosted inside the Orders service.

### UI Capabilities
- View products & inventory
- Create orders
- Trigger payment success/failure
- View order status
- View **clean saga timelines**
- Ask ShopAgent questions

> This UI is intentionally minimal and exists only for **debugging, demos, and interviews**.

---

## 🏗️ Tech Stack

- FastAPI
- SQLAlchemy + Alembic
- PostgreSQL
- Redis (Streams + Celery broker)
- Celery + Celery Beat
- Docker & Docker Compose
- OpenRouter (LLM intent classification)
- Jinja2 (debug UI)

---

## 🚀 Local Development (Docker Compose)

### 1️⃣ Create a `.env` file

```
POSTGRES_USER=shopstream
POSTGRES_PASSWORD=shopstream
POSTGRES_DB=shopstream
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379

OPENROUTER_API_KEY=your-openrouter-key
```

### 2️⃣ Start the stack

```
docker compose up --build
```

Open the UI at:
```
http://localhost:8000/ui/products
```

---

## 🧠 What This Project Demonstrates

- Event-driven backend design
- Saga choreography (not orchestration)
- Outbox pattern for reliability
- Idempotent consumers
- Compensation-based failure handling
- Safe, bounded agentic AI
- Debug-first observability

---

## 📄 License

MIT License
