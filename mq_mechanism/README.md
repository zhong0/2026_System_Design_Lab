# 搶加薪 · MQ Mechanism Demo

一個用來現場展示 **Message Queue (RabbitMQ) + Event Streaming (Kafka)** 運作機制的技術 Demo。
主題：**「搶加薪」** — 每輪只有 3 個名額，觀眾用手機掃 QR Code 進來搶，投影幕即時顯示誰搶到、queue 現況、以及 async / sync 兩種模式的差異。

---

## 系統概觀

### 服務清單

| Service | Port | 角色 |
|---|---|---|
| `raise_grab_service` | `1001` | 接收使用者的搶名額 API；async 模式把 request publish 到 RabbitMQ；sync 模式在 process 內用 `asyncio.Lock` + `sleep` 直接處理 |
| `grab_worker_service` | — | 從 RabbitMQ 消費 grab request，決定 win / lost，把結果 publish 到 Kafka；同時另開一條連線監聽 `grab_control` queue 處理 pause / resume / reset |
| `event_log_service` | `1003` | 從 Kafka 消費兩個 topic (`grab_requests_log`, `grab_results_log`) 透過 **WebSocket 推播**給 dashboard 與所有手機端；同時 serve `grab.html`（手機）與 `index.html`（投影幕） |
| `rabbitmq` | `5672 / 15672` | 業務 queue：`grab_requests`；控制 queue：`grab_control` |
| `kafka` | `9092` | 兩個 topic：`grab_requests_log`（請求事件流）、`grab_results_log`（結果事件流） |
| `kafka_ui` | `1004` | Provectus Kafka UI，讓觀眾看到 topic / partition / message |

> RabbitMQ Management UI：`http://<host>:15672`（帳密 `guest / guest`）
> Kafka UI：`http://<host>:1004`

### Async pipeline（有 queue）

```
手機 POST /grab
  → raise_grab_service
    → RabbitMQ (grab_requests)
      → grab_worker_service（sleep 1.5s → 判斷 win/lost）
        → Kafka (grab_requests_log / grab_results_log)
          → event_log_service（aiokafka consumer）
            → WebSocket 推播
              → dashboard + 中獎者手機
```

### Sync pipeline（沒有 queue，用來對比）

```
手機 POST /grab-sync
  → raise_grab_service.syncGrabSvc
    → asyncio.Lock + asyncio.sleep(1.5)
    → 直接回傳 HTTP response（win / lost）

dashboard 每 1 秒 polling GET /sync/state 更新畫面
```

兩條 pipeline 各自有獨立的 3 個名額狀態池，處理時間都設為 **1500ms** 以求公平比較。

### Master Mode 切換

Dashboard 上有 `CLIENT MODE` 切換鈕：
- 呼叫 `POST /mode` → `event_log_service.wsManager.set_mode()` → 透過 WebSocket 廣播 `{"type": "mode", "mode": "sync"|"async"}` 給**所有連線中的手機**
- 手機收到後立刻切換模式，`GRAB` 按鈕的行為改變（打不同 endpoint、渲染不同 pipeline 動畫）

### DEMO MODE（worker pause / resume）

Dashboard 上的 `⏸ PAUSE` 按鈕會發 `POST /control/pause` → publish 到 `grab_control` queue → worker 收到後 `basic_cancel` 主 consumer；此時 request 會**堆積在 RabbitMQ**（可從 RabbitMQ Management 或 Kafka UI 看到），按 `▶ RESUME` 後才會被消化，這是整場 demo 的高潮。

### 一人一次限制

`grab.html` 在成功搶到後會 lockout 輸入欄與按鈕，直到 **重新整理頁面** 才能再搶一次。

---

## 常用指令

### 啟動 / 重啟全部服務

```bash
cd /Users/zhong/Desktop/my_lab/2026_System_Design_Lab/mq_mechanism

# 冷啟動
docker compose up -d

# 全部重建 image + 起服務（改過 Dockerfile / requirements 時）
docker compose up -d --build

# 全部停掉
docker compose down

# 看日誌
docker compose logs -f raise_grab_service
docker compose logs -f grab_worker_service
docker compose logs -f event_log_service
```

### 遇過的重啟坑（很重要！）

因為 `docker-compose.yml` 有把 code volume mount 進去 (`./raise_grab_service:/app`)，改 Python code 後 **檔案雖然同步進 container，但已經在跑的 Python process 是舊的**（uvicorn 沒開 `--reload`）。所以改完 code 一定要 restart 對應服務：

```bash
# 改完 raise_grab_service 的 code
docker compose restart raise_grab_service

# 改完 grab_worker_service 的 code
docker compose restart grab_worker_service

# 改完 event_log_service 的 code（含前端 html）
docker compose restart event_log_service
```

### 啟動順序問題（RabbitMQ / Kafka 還沒 ready）

`depends_on` 只保證容器啟動順序，不保證服務內部真的 ready。曾經遇到：

| 症狀 | 根因 | 解法 |
|---|---|---|
| `POST /grab` 回 `{"error_code":"grab-error-1","error_message":"failed to enqueue grab request"}` | `raise_grab_service` 比 RabbitMQ 早起來，`rabbitmq_connection.channel` 是 `None` | `docker compose restart raise_grab_service` |
| `event_log_service` 起不來，log 顯示 `aiokafka` connection refused / `Application startup failed. Exiting.` | Kafka broker 還沒 ready | 等 Kafka 完全 ready 後 `docker compose restart event_log_service` |
| SPOT 1~3 空的但一按 `GRAB` 就顯示 `TOO SLOW` / RESET 沒作用 | worker 是舊的 Python process（改 code 後沒 restart） | `docker compose restart grab_worker_service` |

**通用排錯 SOP**：改過 code 或看到怪症狀 → 先看容器啟動時間 vs. 檔案 mtime → 有差就 restart 該服務。

```bash
# 檢查容器啟動時間
docker ps --format '{{.Names}}\t{{.Status}}'

# 檢查 code 最後修改時間
ls -la raise_grab_service/service/
```

---

## 查 IP（讓手機連得到）

Demo 時投影幕跑 dashboard、手機要連 raise_grab_service。**手機和電腦必須在同一 Wi-Fi**。

### macOS 查本機 IP

```bash
# 方法一（推薦，直接印出 Wi-Fi IP）
ipconfig getifaddr en0

# 方法二（有線網路試 en1）
ipconfig getifaddr en1

# 方法三（列出全部 interface）
ifconfig | grep "inet " | grep -v 127.0.0.1
```

假設拿到 `192.168.1.42`：
- **手機掃 QR Code / 打 URL**：`http://192.168.1.42:1003/`（進 `grab.html`）
- **投影幕 dashboard**：`http://192.168.1.42:1003/dashboard`
- **Kafka UI（給觀眾看 queue）**：`http://192.168.1.42:1004`
- **RabbitMQ Management**：`http://192.168.1.42:15672`（`guest / guest`）

> 前端 JS 用 `window.location.hostname` 動態組 API base（`http://<host>:1001`），所以不用寫死 IP，手機只要能連到 `1003` 就自動連得到 `1001`。

### 產 QR Code 給觀眾掃

```bash
# 用 qrencode 直接在 terminal 印一個
brew install qrencode
qrencode -t ansiutf8 "http://192.168.1.42:1003/"
```

---

## Demo 建議流程

1. 開場：投影 `http://<ip>:1003/dashboard`，讓大家看到 3 個空 SPOT + ASYNC / SYNC 兩塊
2. QR Code 貼牆上，觀眾用手機進 `http://<ip>:1003/`
3. **第一輪（ASYNC + PAUSE 演示）**：按 `⏸ PAUSE` → 讓觀眾狂搶 → 開 Kafka UI / RabbitMQ Management 讓大家看訊息堆積 → 按 `▶ RESUME` → SPOT 依序被搶下
4. `RESET` 清空
5. **第二輪（SYNC 對比）**：dashboard 切到 SYNC → 觀眾同時搶 → 看到 dashboard 是「1 秒才更新一次」的 polling 效果（有明顯延遲感），且 sync 的 request 因為在 web process 內排隊會愈來愈久
6. `RESET` 清空、切回 ASYNC 收尾
