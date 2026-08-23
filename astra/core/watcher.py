from __future__ import annotations

import threading
from pathlib import Path
from time import monotonic
from typing import Any

from .engine import AstraEngine


class AstraWatcher:
    """Poll a workspace and refresh Astra artifacts when files change."""

    def __init__(self, root: str | Path, interval: float = 1.0) -> None:
        self.root = Path(root).resolve()
        self.interval = interval
        self.engine = AstraEngine(self.root)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._snapshot: dict[str, tuple[int, int]] = {}
        self._last_indexed: float | None = None
        self._last_error: str | None = None
        self._index_count = 0

    def start(self) -> dict[str, Any]:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return self.status()
            self._stop_event.clear()
            self._refresh_snapshot()
            self._index()
            self._thread = threading.Thread(target=self._run, name="astra-watcher", daemon=True)
            self._thread.start()
            return self.status()

    def stop(self) -> dict[str, Any]:
        self._stop_event.set()
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=max(self.interval * 2, 1.0))
        self._thread = None
        return self.status()

    def status(self) -> dict[str, Any]:
        thread = self._thread
        return {
            "root": str(self.root),
            "running": bool(thread and thread.is_alive()),
            "interval": self.interval,
            "last_indexed": self._last_indexed,
            "index_count": self._index_count,
            "last_error": self._last_error,
        }

    def wait(self) -> None:
        self._stop_event.wait()

    def _run(self) -> None:
        while not self._stop_event.wait(self.interval):
            try:
                current = self._file_snapshot()
                if current != self._snapshot:
                    self._snapshot = current
                    self._index()
            except Exception as exc:
                self._last_error = str(exc)

    def _index(self) -> None:
        try:
            self.engine.index()
            self._last_indexed = monotonic()
            self._index_count += 1
            self._last_error = None
        except Exception as exc:
            self._last_error = str(exc)

    def _refresh_snapshot(self) -> None:
        self._snapshot = self._file_snapshot()

    def _file_snapshot(self) -> dict[str, tuple[int, int]]:
        snapshot: dict[str, tuple[int, int]] = {}
        for path in self.engine.parser.discover(self.root):
            try:
                stat = path.stat()
            except OSError:
                continue
            relative = path.relative_to(self.root).as_posix()
            snapshot[relative] = (stat.st_mtime_ns, stat.st_size)
        return snapshot
