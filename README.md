# System Design Study Group — Side Project Lab

As an Engineering Manager, I am leading a system design reading club within the team, with the goal of building deeper technical foundations through structured discussion and hands-on experimentation.

Each member is assigned topics to research and explore through small-scale side projects. This repository contains my own assigned topics and experiments. Each subdirectory has its own README with detailed notes and implementation specifics.

---

## Assigned Topics

| Date | Topic | Description |
|------|-------|-------------|
| 2026/03/13 | **Traffic Forwarding** | An omikuji-inspired fortune drawing app that routes traffic through Nginx → Kong → load-balanced backends |
| 2026/05/08 | **Cache** | A URL shortener demonstrating the cache-aside pattern with Redis in front of PostgreSQL |
| 2026/07/03 | **Message Queue** | A "Grab a Raise" demo contrasting async (RabbitMQ + Kafka) and sync request pipelines |

---

## Repository Structure

```
.
├── traffic_forwarding_mechanism   # Traffic forwarding: Nginx + Kong + load-balanced services
├── cache_mechanism                # Caching: cache-aside URL shortener (Redis + PostgreSQL)
├── mq_mechanism                   # Message queue: "Grab a Raise" demo (RabbitMQ + Kafka)
└── README.md
```

Each subdirectory has its own README with setup instructions and design notes.

## References
 
- *Grokking the System Design Interview*
