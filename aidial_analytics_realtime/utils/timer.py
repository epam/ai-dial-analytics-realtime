import time
from typing import Callable


class Timer:
    start: float
    format: str
    printer: Callable[[str], None]

    def __init__(
        self,
        printer: Callable[[str], None] = print,
        *,
        format: str = "{elapsed}",
    ):
        self.format = format
        self.printer = printer

    def _elapsed(self) -> str:
        elapsed = time.perf_counter() - self.start
        return f"{elapsed:.3f}s"

    def _on_enter(self):
        self.start = time.perf_counter()
        return self

    def _on_exit(self):
        self.printer(self.format.format(elapsed=self._elapsed()))

    async def __aenter__(self):
        return self._on_enter()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._on_exit()

    def __enter__(self):
        return self._on_enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._on_exit()
