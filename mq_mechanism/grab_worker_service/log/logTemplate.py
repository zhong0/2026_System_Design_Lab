import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import ClassVar


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "logger": record.name,
                "timestamp": datetime.fromtimestamp(
                    record.created, tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "level": record.levelname,
                "function": record.funcName,
                "line": record.lineno,
                "message": record.getMessage(),
                "file": record.filename,
            },
            ensure_ascii=False,
        )


class _DateRotationFilter(logging.Filter):
    def __init__(self, owner: "JSONLogger") -> None:
        super().__init__()
        self._owner = owner

    def filter(self, record: logging.LogRecord) -> bool:
        today = datetime.now(timezone.utc).date()
        if self._owner.current_date != today:
            self._owner._rebuild_handler(today)
            self._owner.current_date = today
        return True


class JSONLogger:
    _instances: ClassVar[dict[str, "JSONLogger"]] = {}
    LOG_DIR = "./log_records"
    RETENTION_DAYS = 7

    def __new__(cls, name: str) -> "JSONLogger":
        if name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[name] = instance
        return cls._instances[name]

    def __init__(self, name: str) -> None:
        if hasattr(self, "_initialized"):
            return

        self.name = name
        self.current_date: date | None = None

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.logger.addFilter(_DateRotationFilter(self))

        self._initialized = True

    def get_logger(self) -> logging.Logger:
        today = datetime.now(timezone.utc).date()
        if self.current_date != today:
            self._rebuild_handler(today)
            self.current_date = today
        return self.logger

    def _rebuild_handler(self, today: date) -> None:
        self._close_handlers()

        os.makedirs(self.LOG_DIR, exist_ok=True)
        log_path = os.path.join(self.LOG_DIR, f"log.{today.strftime('%Y-%m-%d')}.log")

        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(_JSONFormatter())
        self.logger.addHandler(handler)

        self._cleanup_old_logs(today)

    def _close_handlers(self) -> None:
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

    def _cleanup_old_logs(self, current_date: date) -> None:
        cutoff = current_date - timedelta(days=self.RETENTION_DAYS)

        try:
            entries = os.listdir(self.LOG_DIR)
        except OSError as exc:
            self.logger.warning("無法列出日誌目錄：%s", exc)
            return

        for filename in entries:
            if not (filename.startswith("log.") and filename.endswith(".log")):
                continue
            try:
                file_date = datetime.strptime(filename[4:14], "%Y-%m-%d").date()
            except ValueError:
                continue

            if file_date < cutoff:
                try:
                    os.remove(os.path.join(self.LOG_DIR, filename))
                except OSError as exc:
                    self.logger.warning("無法刪除舊日誌 %s：%s", filename, exc)
