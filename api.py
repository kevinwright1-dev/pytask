from fastapi import FastAPI
from pydantic import BaseModel
from pytask.broker.redis import RedisBroker
from pytask.broker.result import RedisResultStore
from pytask.task import configure
import uuid

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
    tasks: list  # list of EnqueueRequests

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
        }
        broker.enqueue(message)
        task_ids.append(task_id)
    return {"task_ids": task_ids}