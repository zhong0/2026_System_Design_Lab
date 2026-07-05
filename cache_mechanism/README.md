# Cache Mechanism

A hands-on lab that demonstrates the **cache-aside (lazy loading) pattern** using a URL shortener as the sample application. Users submit a long URL and receive a short code; resolving that code redirects to the original URL. Every lookup goes through Redis first and falls back to PostgreSQL only on a cache miss, so you can directly observe the latency difference between a cache hit and a database read.

The goal is to show how a fast in-memory cache (Redis) sits in front of a durable system of record (PostgreSQL), how entries are populated and expired (TTL), and how an LRU eviction policy behaves under a tight memory limit.

---

## What It Demonstrates

- **Cache-aside reads** — on lookup, the service checks Redis first. On a hit it returns immediately; on a miss it reads PostgreSQL, then back-fills Redis before returning.
- **Write-through on create** — when a short link is created, it is written to PostgreSQL and immediately cached in Redis.
- **TTL expiration** — cache entries expire after `CACHE_TTL` seconds (configurable), forcing a fresh database read afterward.
- **LRU eviction** — Redis is deliberately capped at a tiny `maxmemory` with an `allkeys-lru` policy, so you can watch least-recently-used entries get evicted.
- **Observable latency** — the `/link/{code}/info` endpoint reports the data source (`redis` vs `postgres`) and the elapsed time, making the hit/miss cost visible in the UI.

---

## Services

The lab is split into two Compose stacks that share one external Docker network.

| Stack | Service | Port | Role |
|---|---|---|---|
| `storage_item` | `postgres` | `5432` | Durable system of record. Holds the `short_links` table (code, original URL, timestamps, expiry). |
| `storage_item` | `redis` | `6379` | Cache layer. Runs with a small `maxmemory` and `allkeys-lru` eviction to make caching effects visible. |
| `short_link_service` | `short_link_service` | `1002` | FastAPI application implementing the cache-aside logic and serving the web UI. |

### Request Flow

```
Client
  → short_link_service (:1002, FastAPI)
      ├── create:  write PostgreSQL ──▶ set Redis (key: short:<code>, TTL)
      └── resolve: read Redis ──hit──▶ return / redirect
                        └──miss──▶ read PostgreSQL ──▶ back-fill Redis ──▶ return
```

`short_link_service` is the only component clients talk to; it orchestrates both the cache (Redis) and the database (PostgreSQL). The `storage_item` stack owns the two backing datastores and must be running first.

---

## How to Run

Both stacks attach to an **external** network (`cache-lab-network`) and the application uses a pre-built image, so create the network and build the image before starting.

```bash
cd cache_mechanism

# 1. Create the shared external network
docker network create cache-lab-network

# 2. Start the datastores (PostgreSQL + Redis)
cd storage_item
docker compose up -d
cd ..

# 3. Build the application image and start the service
docker build -t cache_mecahnime_lab:dev-1.0.0 ./short_link_service
cd short_link_service
docker compose up -d
```

> The stacks read PostgreSQL/Redis credentials (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `POSTGRES_DB`) from a `.env` file. Provide one before starting, and make sure the same values are used by both stacks.
>
> The `short_links` table is defined in `storage_item/init.sql`; apply it to the database on first run.

Open the UI at **`http://localhost:1002/static/ui`**.

### Key Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/static/ui` | The web UI (shows current cache TTL). |
| `POST` | `/create_short_link` | Create a short link. Body: `{ "urlLink": "https://..." }`. |
| `GET` | `/{code}` | Resolve a code and HTTP-redirect to the original URL (cache-aside). |
| `GET` | `/link/{code}/info` | Return the URL plus its source (`redis`/`postgres`) and elapsed time — the hit/miss demo endpoint. |
