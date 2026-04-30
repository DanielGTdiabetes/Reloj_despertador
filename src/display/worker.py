from __future__ import annotations

import queue
import threading
from typing import Any, Protocol


class RenderableDisplay(Protocol):
    def render(self, image: Any) -> None: ...
    def cleanup(self) -> None: ...


class DisplayWorker:
    def __init__(self, name: str, display: RenderableDisplay, spi_lock: threading.Lock | None = None) -> None:
        self.name = name
        self.display = display
        self.spi_lock = spi_lock or threading.Lock()

        self._frames: queue.Queue[Any] = queue.Queue(maxsize=1)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name=f"display-{name}", daemon=True)

        self.healthy = True
        self.failures = 0
        self.last_error = ""

    def start(self) -> None:
        self._thread.start()

    def submit(self, image: Any) -> None:
        if not self.healthy or image is None:
            return

        try:
            self._frames.put_nowait(image)
            return
        except queue.Full:
            pass

        try:
            _ = self._frames.get_nowait()
        except queue.Empty:
            pass

        try:
            self._frames.put_nowait(image)
        except queue.Full:
            # In the worst case, drop the frame.
            return

    def stop(self) -> None:
        self._stop.set()

    def cleanup(self) -> None:
        self.stop()
        try:
            self._thread.join(timeout=1.5)
        except Exception:
            pass

        try:
            with self.spi_lock:
                self.display.cleanup()
        except Exception as exc:
            print(f"[Display:{self.name}] cleanup failed: {exc}")

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                image = self._frames.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                with self.spi_lock:
                    self.display.render(image)
                self.failures = 0
                self.last_error = ""
            except Exception as exc:
                self.failures += 1
                self.last_error = str(exc)
                print(f"[Display:{self.name}] render failed ({self.failures}): {exc}")
                if self.failures >= 3:
                    self.healthy = False
                    print(f"[Display:{self.name}] disabled after repeated failures")

