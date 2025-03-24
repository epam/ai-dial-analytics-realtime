import asyncio
import contextvars
import functools
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, ParamSpec, TypeVar

_T = TypeVar("_T")
_P = ParamSpec("_P")

cpu_task_executor = ThreadPoolExecutor()


async def run_in_cpu_tasks_executor(
    func: Callable[_P, _T], *args: _P.args, **kwargs: _P.kwargs
) -> _T:
    loop = asyncio.get_event_loop()
    ctx = contextvars.copy_context()
    func_call = functools.partial(ctx.run, func, *args, **kwargs)
    return await loop.run_in_executor(cpu_task_executor, func_call)  # type: ignore
