"""Sequential dependency scheduler with cooperative cancellation and durable states."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import Event
from typing import Callable
from uuid import uuid4

from .storage import Store


class Cancelled(Exception):
    pass


@dataclass
class Task:
    name: str
    run: Callable
    depends: tuple[str, ...] = ()
    weight: float = 1


@dataclass
class Context:
    cancel: Event
    report: Callable
    values: dict = field(default_factory=dict)

    def check(self):
        if self.cancel.is_set():
            raise Cancelled("İşlem iptal edildi; tamamlanan cache korunuyor")


class Scheduler:
    def __init__(self, store: Store):
        self.store = store
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="vex-job")
        self.cancel_event = Event()
        self.future = None

    def start(self, tasks: list[Task], notify: Callable):
        if self.future and not self.future.done():
            raise RuntimeError("Önce aktif işlemin bitmesini bekleyin")
        names = [t.name for t in tasks]
        if not tasks or len(names) != len(set(names)) or any(t.weight <= 0 for t in tasks):
            raise ValueError("Görev adları benzersiz, ağırlıkları pozitif olmalı")
        seen = set()
        for task in tasks:
            if not set(task.depends) <= seen:
                raise ValueError("Görev bağımlılıkları sıralı olmalı")
            seen.add(task.name)
        self.cancel_event = Event()
        job_id = str(uuid4())
        self.store.job(job_id, ", ".join(names), "PENDING")
        self.future = self.pool.submit(self._run, job_id, tasks, notify, self.cancel_event)
        return self.future

    def _run(self, job_id, tasks, notify, cancel):
        done_weight = 0
        total = sum(t.weight for t in tasks)
        values = {}
        progress = 0
        last_record = -1
        try:
            for task in tasks:
                def report(fraction, message):
                    nonlocal progress, last_record
                    if not 0 <= fraction <= 1:
                        raise ValueError("Geçersiz ilerleme")
                    progress = (done_weight + task.weight * fraction) / total
                    if int(progress * 100) != last_record:
                        self.store.job(job_id, task.name, "RUNNING", progress)
                        last_record = int(progress * 100)
                    notify("RUNNING", progress, message)
                context = Context(cancel, report, values)
                context.check()
                report(0, task.name)
                values[task.name] = task.run(context)
                context.check()
                report(1, task.name)
                done_weight += task.weight
            self.store.job(job_id, ", ".join(t.name for t in tasks), "COMPLETED", 1)
            notify("COMPLETED", 1, "İşlem tamamlandı")
            return values
        except Exception as exc:
            status = "CANCELLED" if isinstance(exc, Cancelled) else "FAILED"
            self.store.job(job_id, ", ".join(t.name for t in tasks), status, progress, str(exc))
            notify(status, progress, str(exc))
            raise

    def cancel(self):
        self.cancel_event.set()

    def close(self):
        self.cancel()
        self.pool.shutdown(wait=False, cancel_futures=True)
