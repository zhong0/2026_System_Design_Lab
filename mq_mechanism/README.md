# Message Queue Mechanism — "Grab a Raise" Demo

A live, interactive demo that shows how a **message queue (RabbitMQ)** and an **event stream (Kafka)** work together to decouple a spike of incoming requests from the work that processes them.

The theme is **"Grab a Raise"**: each round has only **3 spots**. The audience scans a QR code on their phones and races to grab a spot. A projector dashboard shows in real time who won, the current queue state, and — most importantly — the difference between an **async (queued)** pipeline and a **sync (no queue)** pipeline.

---

## What It Demonstrates

- **Async pipeline with a queue** — requests are published to RabbitMQ and consumed by a worker at a controlled rate. A spike of clicks is absorbed by the queue instead of overwhelming the app.
- **Sync pipeline without a queue** — the same logic handled inline inside the web process (`asyncio.Lock` + `sleep`), shown side by side so the audience feels the latency and back-pressure difference.
- **Event streaming for observability** — every request and every result is emitted to Kafka topics, then pushed to all connected browsers over WebSocket, so the dashboard and phones update live.
- **Back-pressure / buffering (the highlight)** — pausing the worker lets requests visibly pile up in RabbitMQ; resuming it drains the backlog and fills the spots in order.
- **Live mode switching** — an operator can flip all connected phones between async and sync mode from the dashboard via a WebSocket broadcast.

---

## Services

| Service | Port | Role |
|---|---|---|
| `raise_grab_service` | `1004` | Receives grab requests. **Async** mode publishes each request to RabbitMQ; **sync** mode handles it inline with `asyncio.Lock` + `sleep`. |
| `grab_worker_service` | — | Consumes grab requests from RabbitMQ, decides win/lost, and publishes the outcome to Kafka. A second connection listens on the `grab_control` queue for pause / resume / reset. |
| `event_log_service` | `1003` | Consumes both Kafka topics and pushes events to the dashboard and phones over **WebSocket**. Also serves `grab.html` (phone) and `index.html` (projector dashboard). |
| `rabbitmq` | `5672` / `15672` | Work queue `grab_requests`; control queue `grab_control`. Management UI on `15672` (`guest / guest`). |
| `kafka` | `9092` | Two topics: `grab_requests_log` (request event stream) and `grab_results_log` (result event stream). |
| `kafka_ui` | `1005` | Provectus Kafka UI — lets the audience watch topics, partitions, and messages. |

### Async Pipeline (with queue)

```
Phone POST /grab
  → raise_grab_service
    → RabbitMQ (grab_requests)
      → grab_worker_service   (processes at a fixed rate → win / lost)
        → Kafka (grab_requests_log / grab_results_log)
          → event_log_service (Kafka consumer)
            → WebSocket push
              → dashboard + winners' phones
```

### Sync Pipeline (no queue, for contrast)

```
Phone POST /grab-sync
  → raise_grab_service (inline: asyncio.Lock + sleep)
    → immediate HTTP response (win / lost)

Dashboard polls GET /sync/state every 1s to refresh
```

Both pipelines keep their own independent pool of 3 spots and use the same **1500 ms** processing time, so the comparison is fair. The only difference is the queue.

`raise_grab_service` is the entry point, `grab_worker_service` is the decoupled processor, and `event_log_service` is the real-time fan-out layer — RabbitMQ sits between the first two, Kafka between the last two.

---

## How to Run

Unlike the other labs, this stack builds its images from source (`build:` in the Compose file) and creates its own bridge network, so a single command brings everything up.

```bash
cd mq_mechanism

# Cold start
docker compose up -d

# Rebuild images + start (after changing a Dockerfile / requirements)
docker compose up -d --build

# Stop everything
docker compose down

# Tail logs
docker compose logs -f raise_grab_service
docker compose logs -f grab_worker_service
docker compose logs -f event_log_service
```

### Access Points

Find the host's LAN IP (phones must be on the same Wi-Fi as the machine):

```bash
ipconfig getifaddr en0   # macOS Wi-Fi IP
```

Assuming the IP is `192.168.1.42`:

| Who | URL |
|---|---|
| Phone (scan QR / grab page) | `http://192.168.1.42:1003/` |
| Projector dashboard | `http://192.168.1.42:1003/dashboard` |
| Kafka UI (show the queue) | `http://192.168.1.42:1005` |
| RabbitMQ Management | `http://192.168.1.42:15672` (`guest / guest`) |

> The front-end derives the API base from `window.location.hostname`, so nothing is hard-coded — a phone that can reach port `1003` will automatically reach `raise_grab_service` on `1004`.

Generate a QR code for the audience:

```bash
brew install qrencode
qrencode -t ansiutf8 "http://192.168.1.42:1003/"
```

---

## Operational Notes

Code is volume-mounted into the containers, but the running Python process is **not** auto-reloaded. After changing code, restart the affected service:

```bash
docker compose restart raise_grab_service   # after editing raise_grab_service
docker compose restart grab_worker_service  # after editing grab_worker_service
docker compose restart event_log_service    # after editing event_log_service (incl. front-end HTML)
```

`depends_on` only orders container startup — it does not wait for RabbitMQ/Kafka to be internally ready. Common startup issues:

| Symptom | Root cause | Fix |
|---|---|---|
| `POST /grab` returns `grab-error-1 / failed to enqueue grab request` | `raise_grab_service` started before RabbitMQ was ready (channel is `None`) | `docker compose restart raise_grab_service` |
| `event_log_service` fails to start (`aiokafka` connection refused / `Application startup failed`) | Kafka broker not ready yet | wait for Kafka, then `docker compose restart event_log_service` |
| Spots stay empty but grabbing shows `TOO SLOW` / RESET does nothing | worker is running stale code (edited without restart) | `docker compose restart grab_worker_service` |

**Troubleshooting rule of thumb:** after editing code or seeing odd behavior, compare the container start time against the file mtime; if they differ, restart that service.

```bash
docker ps --format '{{.Names}}\t{{.Status}}'   # container start times
ls -la raise_grab_service/service/             # code mtimes
```

---

## Suggested Demo Flow

1. Project `http://<ip>:1003/dashboard` — 3 empty spots, ASYNC and SYNC panels side by side.
2. Post the QR code; audience opens `http://<ip>:1003/` on their phones.
3. **Round 1 (ASYNC + PAUSE):** press `⏸ PAUSE`, let everyone grab, open Kafka UI / RabbitMQ Management to show messages piling up, then `▶ RESUME` — spots fill in order. This is the highlight.
4. `RESET` to clear.
5. **Round 2 (SYNC contrast):** switch the dashboard to SYNC; everyone grabs at once and the audience sees the 1-second polling lag and growing queue time inside the web process.
6. `RESET`, switch back to ASYNC, and wrap up.
