import asyncio
import contextvars
import functools
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

cpu_task_executor = ThreadPoolExecutor()


async def run_in_cpu_tasks_executor[**P, T](
    func: Callable[P, T], *args: P.args, **kwargs: P.kwargs
) -> T:
    loop = asyncio.get_event_loop()
    ctx = contextvars.copy_context()
    func_call = functools.partial(ctx.run, func, *args, **kwargs)
    return await loop.run_in_executor(cpu_task_executor, func_call)  # type: ignore
