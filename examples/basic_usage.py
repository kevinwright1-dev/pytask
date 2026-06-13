from pytask.task import task, configure
from pytask.broker.redis import RedisBroker
from pytask.broker.worker import WorkerPool
from pytask.broker.result import RedisResultStore
import time

broker = RedisBroker()
configure(broker)
result_store = RedisResultStore()
worker = WorkerPool(broker, 3)
worker.start()

@task
def add(a, b):
    return a+b

@task
def sub(a, b):
    return a-b

@task
def mult(a, b):
    return a*b

@task
def say_hello():
    print("Hello")

id1 = add.delay(6, 3)
id2 = sub.delay(6, 3)
id3 = mult.delay(6, 3)
id4 = say_hello.delay()

time.sleep(3)

print(result_store.get_result(id1))
print(result_store.get_result(id2))
print(result_store.get_result(id3))
print(result_store.get_result(id4))

worker.stop()

