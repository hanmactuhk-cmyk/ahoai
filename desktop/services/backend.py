import time
import uuid
from typing import Dict, Any
import requests


class BackendError(Exception):
    pass


class DemoBackend:
    """Offline backend: app works immediately without an external service."""

    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(self, prompt, duration, aspect):
        job_id = "demo-" + uuid.uuid4().hex[:10]
        self.jobs[job_id] = {
            "id": job_id,
            "prompt": prompt,
            "duration": duration,
            "aspect": aspect,
            "status": "queued",
            "progress": 0,
            "created_at": time.time(),
        }
        return dict(self.jobs[job_id])

    def get_job(self, job_id):
        job = self.jobs.get(job_id)
        if not job:
            raise BackendError("Không tìm thấy job.")
        if job["status"] not in ("completed", "cancelled", "failed"):
            # Fast enough for a visible demo, no external network required.
            job["progress"] = min(100, int((time.time() - job["created_at"]) * 50))
            if job["progress"] >= 100:
                job["status"] = "completed"
        return dict(job)

    def cancel_job(self, job_id):
        job = self.jobs.get(job_id)
        if not job:
            raise BackendError("Không tìm thấy job.")
        job["status"] = "cancelled"
        return dict(job)


class ApiBackend:
    """Authorized REST adapter.

    Expected endpoints:
      POST /jobs
      GET  /jobs/{id}
      POST /jobs/{id}/cancel
    """

    def __init__(self, base_url, api_key, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key.strip()
        self.timeout = timeout

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = "Bearer " + self.api_key
        return h

    def _request(self, method, path, **kwargs):
        if not self.base_url:
            raise BackendError("Chưa cấu hình Base URL.")
        try:
            r = requests.request(
                method,
                self.base_url + path,
                headers=self._headers(),
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as e:
            raise BackendError(f"Lỗi kết nối API: {e}") from e

        if r.status_code >= 400:
            raise BackendError(f"API HTTP {r.status_code}: {r.text[:300]}")

        if not r.content:
            return {}

        try:
            return r.json()
        except ValueError as e:
            raise BackendError("API trả JSON không hợp lệ.") from e

    def create_job(self, prompt, duration, aspect):
        data = self._request(
            "POST", "/jobs",
            json={"prompt": prompt, "duration": duration, "aspect": aspect}
        )
        if not data.get("id"):
            raise BackendError("API không trả về id.")
        return data

    def get_job(self, job_id):
        return self._request("GET", f"/jobs/{job_id}")

    def cancel_job(self, job_id):
        return self._request("POST", f"/jobs/{job_id}/cancel")


def make_backend(config):
    if str(config.get("mode", "demo")).lower() == "api":
        return ApiBackend(config.get("base_url", ""), config.get("api_key", ""))
    return DemoBackend()
