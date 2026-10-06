"""One bounded task pool and controller queue per backend, not per run."""
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Full
from threading import BoundedSemaphore, Lock, Thread

from .models import WorkflowError


class TaskBudget:
    def __init__(self, max_workers: int, max_pending: int | None = None):
        self.max_workers = max_workers
        self.max_pending = max_pending or max_workers * 4
        self._permits = BoundedSemaphore(self.max_pending)
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="fusionlab-tool")
        self._lock = Lock()
        self._admitted = self._active = 0

    def reserve(self) -> bool:
        if not self._permits.acquire(blocking=False): return False
        with self._lock: self._admitted += 1
        return True

    def submit(self, function, *args):
        def invoke():
            with self._lock: self._active += 1
            try: return function(*args)
            finally:
                with self._lock: self._active -= 1
        def release(_future):
            with self._lock: self._admitted -= 1
            self._permits.release()
        future = self._pool.submit(invoke)
        future.add_done_callback(release)
        return future

    def release_reservation(self):
        with self._lock: self._admitted -= 1
        self._permits.release()

    def state(self):
        with self._lock:
            return {"max_workers": self.max_workers, "max_admitted_tasks": self.max_pending,
                "active_tasks": self._active, "queued_tasks": self._admitted - self._active, "gpu_slots": 1,
                "memory_limit_supported": False}


class RunDispatcher:
    def __init__(self, engine, *, controllers: int = 2, queue_limit: int = 64):
        self.engine = engine
        self._queue = Queue(maxsize=queue_limit)
        self._ids: set[str] = set()
        self._lock = Lock()
        for _ in range(controllers):
            Thread(target=self._work, daemon=True, name="fusionlab-run-controller").start()

    def submit(self, run_id: str, *, retry: bool = False, node_id: str | None = None) -> bool:
        with self._lock:
            if run_id in self._ids: return False
            self._ids.add(run_id)
            try: self._queue.put_nowait((run_id, retry, node_id))
            except Full:
                self._ids.remove(run_id)
                raise WorkflowError("backend_run_queue_full", status_code=429)
        return True

    def _work(self):
        while True:
            run_id, retry, node_id = self._queue.get()
            try:
                self.engine.run(run_id, retry_failed=retry, retry_node_id=node_id)
            except Exception as exc:
                self.engine.store.event(run_id, "dispatch_error", self.engine.disclosure.diagnostic(exc))
            finally:
                with self._lock: self._ids.remove(run_id)
                self._queue.task_done()

    def state(self):
        with self._lock:
            return {"queued_runs": self._queue.qsize(), "accepted_runs": len(self._ids), "queue_limit": self._queue.maxsize}
