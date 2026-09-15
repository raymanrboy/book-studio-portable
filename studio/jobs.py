"""Background jobs with progress reporting, polled by the UI."""
from __future__ import annotations

import threading
import time
import traceback
from typing import Any, Callable

from . import core


class UserError(Exception):
    """Expected failure with a human-readable (Ukrainian) message."""


class JobError(UserError):
    pass


class Job:
    def __init__(self, kind: str) -> None:
        self.id = core.new_id()[:12]
        self.kind = kind
        self.status = "running"
        self.step = "Підготовка…"
        self.percent = 0.0
        self.detail = ""
        self.result: Any = None
        self.error: str | None = None
        self.started = time.time()
        self.finished: float | None = None
        self._lock = threading.Lock()

    def progress(self, step: str | None = None, percent: float | None = None, detail: str | None = None) -> None:
        with self._lock:
            if step is not None:
                self.step = step
            if percent is not None:
                self.percent = max(0.0, min(100.0, float(percent)))
            if detail is not None:
                self.detail = detail

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "id": self.id,
                "kind": self.kind,
                "status": self.status,
                "step": self.step,
                "percent": round(self.percent, 1),
                "detail": self.detail,
                "result": self.result,
                "error": self.error,
                "elapsed": round((self.finished or time.time()) - self.started, 1),
            }


class Jobs:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._exclusive: dict[str, str] = {}
        self._lock = threading.Lock()

    def start(self, kind: str, fn: Callable[[Job], Any], exclusive: str | None = None) -> Job:
        with self._lock:
            if exclusive:
                running = self._jobs.get(self._exclusive.get(exclusive, ""))
                if running and running.status == "running":
                    raise JobError("Ця операція вже виконується. Дочекайтеся її завершення.")
            job = Job(kind)
            self._jobs[job.id] = job
            if exclusive:
                self._exclusive[exclusive] = job.id
            self._gc()

        def run() -> None:
            try:
                result = fn(job)
                with job._lock:
                    job.result = result
                    job.status = "done"
                    job.percent = 100.0
            except UserError as err:
                with job._lock:
                    job.status = "error"
                    job.error = str(err)
            except Exception as err:  # unexpected — keep details in the log
                core.log.error("Job %s failed:\n%s", kind, traceback.format_exc())
                with job._lock:
                    job.status = "error"
                    job.error = f"Несподівана помилка: {err}"
            finally:
                job.finished = time.time()

        threading.Thread(target=run, name=f"job-{kind}", daemon=True).start()
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def running(self, exclusive: str) -> Job | None:
        job = self._jobs.get(self._exclusive.get(exclusive, ""))
        return job if job and job.status == "running" else None

    def any_running(self) -> bool:
        return any(j.status == "running" for j in list(self._jobs.values()))

    def _gc(self) -> None:
        cutoff = time.time() - 3600
        for key in [k for k, j in self._jobs.items() if j.finished and j.finished < cutoff]:
            del self._jobs[key]


jobs = Jobs()
