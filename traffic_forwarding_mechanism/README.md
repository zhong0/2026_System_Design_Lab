# Traffic Forwarding Mechanism

A hands-on lab that demonstrates how a request is routed through multiple **traffic-forwarding layers** (reverse proxy → API gateway → load-balanced upstreams) before reaching the application. The demo application is an *omikuji*-style fortune drawing game: users draw a random fortune, and every time someone draws the top prize (`大吉` / "Great Blessing") it is counted on a shared leaderboard.

The goal is to show, end to end, how a single public entry point (Nginx on port `80`) can fan traffic out across several identical backend instances via an API gateway (Kong), and how those stateless instances share state through a common Redis store.

---

## What It Demonstrates

- **Reverse proxy** — Nginx accepts all inbound traffic on port `80` and forwards it to Kong, propagating the real client IP (`X-Real-IP`, `X-Forwarded-For`).
- **API gateway + load balancing** — Kong receives proxied traffic on port `8000` and distributes requests across three identical `fortune_service` instances.
- **Horizontal scaling with shared state** — the fortune instances are stateless; each draw result is persisted to Redis, so any instance can serve any request. The API response includes the serving instance's IP so you can watch the load balancing happen in real time.
- **Read/aggregation service** — a separate `leaderboard_service` reads the shared Redis sorted set to render a live "Great Blessing" ranking board.

---

## Services

| Service | Internal Port | Role |
|---|---|---|
| `nginx` | `80` (exposed) | Reverse proxy / single public entry point. Forwards everything to Kong. |
| `kong` | `8000` proxy, `8001` admin, `8002` GUI (all exposed) | API gateway; routes requests and load-balances across the fortune instances. |
| `kong-database` | — | PostgreSQL backing store for Kong's configuration. |
| `kong-migration` | — | One-shot job that bootstraps the Kong database schema. |
| `fortune_service_1/2/3` | `1001` | Three identical FastAPI instances. `POST /fortune` draws a weighted-random fortune; a `大吉` is recorded in Redis. Returns the serving instance IP. |
| `leaderboard_service` | `1001` | FastAPI service. `GET /leaderboard` returns the top drawers; `GET /leaderboard/ui` serves the dashboard page. |
| `redis` | `6379` | Shared state store. A sorted set (`fortune:大吉`) counts wins per user via `ZINCRBY`. |

### Request Flow

```
Client
  → Nginx        (:80, reverse proxy)
    → Kong       (:8000, API gateway + load balancer)
      ├─→ fortune_service_1  (:1001)  ┐
      ├─→ fortune_service_2  (:1001)  ├─ round-robin, all stateless
      └─→ fortune_service_3  (:1001)  ┘
            │
            └─→ Redis (:6379)  ← shared "大吉" leaderboard (sorted set)
                  ↑
      leaderboard_service (:1001) reads the same sorted set for the dashboard
```

Because all three fortune instances write to the same Redis sorted set, and the leaderboard service reads from it, the ranking stays consistent no matter which instance handled a given draw.

---

## How to Run

The Compose file attaches to an **external** Docker network and uses a pre-built application image, so create the network and build the image before starting.

```bash
cd traffic_forwarding_mechanism

# 1. Create the external network the compose file expects
docker network create traffic-forwarding-lab-nework

# 2. Build the shared application image (used by both fortune and leaderboard services)
docker build -t traffic_forwarding_lab:dev-1.0.0 ./fortune_service

# 3. Start everything
docker compose up -d
```

Kong is database-backed and starts with no routes configured. After the stack is up, register the fortune upstream and the leaderboard route through the Kong Admin API (`http://localhost:8001`) so that Nginx → Kong traffic reaches the backends.

Once routes are configured, all traffic enters through **`http://localhost/`** (Nginx). You can also reach Kong's proxy directly on `http://localhost:8000` and its admin GUI on `http://localhost:8002`.

### Key Endpoints (behind the gateway)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/fortune` | Draw a fortune. Body: `{ "username": "..." }`. Returns the fortune and the serving instance IP. |
| `GET` | `/leaderboard` | Top-10 `大吉` drawers as JSON. |
| `GET` | `/leaderboard/ui` | The live leaderboard dashboard page. |
