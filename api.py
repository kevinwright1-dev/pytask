from fastapi import FastAPI
from pydantic import BaseModel
from pytask.broker.redis import RedisBroker
from pytask.broker.result import RedisResultStore
from pytask.task import configure
import uuid
import json

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

broker = RedisBroker()
configure(broker)
result_store = RedisResultStore()

# describes what a single enqueue request looks like
class EnqueueRequest(BaseModel):
    fn: str
    args: list = []
    kwargs: dict = {}

class BatchRequest(BaseModel):
    tasks: list[EnqueueRequest]

class TaskResultsRequest(BaseModel):
    task_ids: list[str]

# endpoint 1
@app.get("/queue/status")
def queue_status():
    # return pending count and dead letter count
    pending_count = broker.r.llen(broker.queue_name)
    dead_letter_count = broker.r.llen("dead_letter")
    return {"pending": pending_count, "dead_letter": dead_letter_count}

# endpoint 2
@app.post("/task/enqueue")
def enqueue_task(request: EnqueueRequest):
    # build the message dict and call broker.enqueue()
    # return the task_id
    task_id = str(uuid.uuid4())
    message = {
        "task_id": task_id,
        "fn": request.fn,
        "args": request.args,
        "kwargs": request.kwargs,
        "attempt": 0,
    }
    broker.enqueue(message)
    return {"task_id": task_id}

# endpoint 3
@app.get("/task/{task_id}")
def get_task(task_id: str):
    # call result_store.get_result(task_id)
    # return it
    result = result_store.get_result(task_id)
    return {"task_id": task_id, "result": result}

@app.post("/tasks/results")
def get_task_results(request: TaskResultsRequest):
    tasks = []
    for task_id in request.task_ids:
        tasks.append({"task_id": task_id, "result": result_store.get_result(task_id)})
    return {"tasks": tasks}

# endpoint 4
@app.post("/task/batch")
def enqueue_batch(request: BatchRequest):
    # loop through request.tasks
    # enqueue each one
    # return list of task ids
    task_ids = []
    for task_request in request.tasks:
        task_id = str(uuid.uuid4())
        message = {
            "task_id": task_id,
            "fn": task_request.fn,
            "args": task_request.args,
            "kwargs": task_request.kwargs,
            "attempt": 0,
        }
        broker.enqueue(message)
        task_ids.append(task_id)
    return {"task_ids": task_ids}

@app.get("/workers")
def get_workers():
    raw = broker.r.hgetall("workers")
    workers = []
    for wid, info_bytes in raw.items():
        info = json.loads(info_bytes)          # None = idle, dict = busy
        workers.append({
            "worker_id": int(wid.decode()),    # b"3" -> 3
            "busy": info is not None,
            "task": info,                      # None, or {task_id, fn, started_at}
        })
    workers.sort(key=lambda w: w["worker_id"])
    return {"workers": workers}
