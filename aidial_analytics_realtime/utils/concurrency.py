import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, ParamSpec, TypeVar

_T = TypeVar("_T")
_P = ParamSpec("_P")

cpu_task_executor = ThreadPoolExecutor()


async def run_in_cpu_tasks_executor(
    func: Callable[_P, _T], *args: _P.args, **kwargs: _P.kwargs
) -> _T:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(cpu_task_executor, func, *args)  # type: ignore
