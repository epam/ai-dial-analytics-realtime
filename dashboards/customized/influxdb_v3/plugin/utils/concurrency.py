from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Protocol, TypeVar

_T = TypeVar("_T")


class Exec(Protocol):
    def run_jobs(self, jobs: Iterable[Callable[[], _T]]) -> list[_T]: ...


class SequentialExec:
    def run_jobs(self, jobs: Iterable[Callable[[], _T]]) -> list[_T]:
        return [job() for job in jobs]


class ThreadPoolExec:
    def __init__(self, max_workers: int = 8):
        self._max_workers = max_workers

    def run_jobs(self, jobs: Iterable[Callable[[], _T]]) -> list[_T]:
        with ThreadPoolExecutor(max_workers=self._max_workers) as ex:
            return list(ex.map(lambda job: job(), jobs))
