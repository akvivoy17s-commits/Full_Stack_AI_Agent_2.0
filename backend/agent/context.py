"""Per-thread task context: cancellation + progress events, usable from any agent code (no-op outside tasks)."""
import threading
from typing import Callable

_local = threading.local()


class Cancelled(BaseException):          # BaseException so broad `except Exception` never swallows it
    pass


class TaskContext:
    def __init__(self, task_id: str, emit: Callable[[str, str, str], None]):
        self.task_id, self.emit, self.cancel = task_id, emit, threading.Event()


def bind(ctx: TaskContext | None) -> None:
    _local.ctx = ctx


def current() -> TaskContext | None:
    return getattr(_local, "ctx", None)


def cancelled() -> bool:
    c = current()
    return bool(c and c.cancel.is_set())


def check() -> None:
    if cancelled():
        raise Cancelled()


def progress(stage: str, msg: str, level: str = "info") -> None:
    c = current()
    if c:
        c.emit(stage, msg, level)
