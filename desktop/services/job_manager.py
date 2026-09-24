import threading
import time
import uuid
from dataclasses import dataclass
from typing import Optional, Callable
from .backend import BackendError, make_backend


@dataclass
class Job:
    local_id: str
    prompt: str
    duration: int
    aspect: str
    remote_id: Optional[str] = None
    status: str = "pending"
    progress: int = 0
    error: str = ""


class JobManager:
    def __init__(self, config, on_update: Callable[[Job], None]):
        self.backend = make_backend(config)
        self.on_update = on_update
        self.jobs = []
        self.stop_event = threading.Event()
        self.worker = None

    def add(self, prompt, duration, aspect):
        job = Job(uuid.uuid4().hex[:8], prompt, duration, aspect)
        self.jobs.append(job)
        self.on_update(job)
        self.start()
        return job

    def start(self):
        if self.worker and self.worker.is_alive():
            return
        self.stop_event.clear()
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()

    def cancel_all(self):
        self.stop_event.set()
        for job in self.jobs:
            if job.status in ("pending", "running"):
                if job.remote_id:
                    try:
                        self.backend.cancel_job(job.remote_id)
                    except Exception:
                        pass
                job.status = "cancelled"
                self.on_update(job)

    def retry(self, local_id):
        for job in self.jobs:
            if job.local_id == local_id:
                job.remote_id = None
                job.status = "pending"
                job.progress = 0
                job.error = ""
                self.on_update(job)
                self.start()
                return

    def _run(self):
        while not self.stop_event.is_set():
            job = next((j for j in self.jobs if j.status == "pending"), None)
            if not job:
                return

            try:
                job.status = "running"
                self.on_update(job)

                created = self.backend.create_job(
                    job.prompt, job.duration, job.aspect
                )
                job.remote_id = str(created["id"])
                self.on_update(job)

                while not self.stop_event.is_set():
                    data = self.backend.get_job(job.remote_id)
                    job.progress = max(0, min(100, int(data.get("progress", 0) or 0)))
                    status = str(data.get("status", "running")).lower()

                    if status in ("completed", "done", "success"):
                        job.status = "completed"
                        job.progress = 100
                        break
                    if status in ("cancelled", "canceled"):
                        job.status = "cancelled"
                        break
                    if status in ("failed", "error"):
                        job.status = "failed"
                        job.error = str(data.get("error", "Backend báo lỗi."))
                        break

                    self.on_update(job)
                    time.sleep(0.5)

                if self.stop_event.is_set() and job.status == "running":
                    job.status = "cancelled"

                self.on_update(job)

            except BackendError as e:
                job.status = "failed"
                job.error = str(e)
                self.on_update(job)
            except Exception as e:
                job.status = "failed"
                job.error = f"Lỗi: {e}"
                self.on_update(job)
