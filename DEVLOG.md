# DEVLOG - pytask

## 2026-05-22

### What I worked on:
Today I started the project by writing the abstract broker class. The abstract class defines the three methods every broker has to implement: enqueue, dequeue, and close. I used Python's ABC module to make it so any broker that doesn't implement all three methods will throw an error.

### What I struggled with:
I was not sure how to force subclasses to implement methods. I learned that using @abstractmethod on each method is how you do that in Python.

### Decision I made:
I decided to write an abstract base class first before writing any real broker so that both the Redis broker and the socket broker would follow the same interface. That way the worker pool can work with either one without knowing which one it is.

### What to do next:
Next I am going to write the Redis broker.

## 2026-05-23

### What I worked on:
Today I worked on the Redis broker. I had to install Redis on my computer. I wrote the enqueue, dequeue, and close methods just like the abstract class. I also used json to serialize the message so Redis can store it as a string.

### What I struggled with:
I learned the difference between json.dump and json.dumps. json.dump writes to a file, json.dumps turns a Python object into a JSON string. I got those confused when trying to serialize the message.

When putting in the parameters for lpush and brpop I used a hardcoded string "queue_name" instead of the actual variable self.queue_name.

I also tried to put __init__ outside of the class because I thought it was just a regular function.

### Decision I made:
I decided to serialize messages using JSON so Redis can store and return them as strings.

### What to do next:
Next I am going to work on the socket broker.

## 2026-05-24

### What I worked on:
Today I wrote the socket broker and a small TCP server to go with it. The server holds the queue as a plain Python list and handles push and pop commands over a network connection. The socket broker connects to that server and uses it the same way the Redis broker uses Redis.

### What I struggled with:
I used port 999 at first and kept getting errors. I found out ports below 1024 are reserved by the OS so I changed it to 9999.

I also forgot to send a response back to the client after a push command, so the client would just hang. Fixed it by sending back an OK message.

I accidentally sent a PUSH command inside the dequeue method instead of POP.

### Decision I made:
I decided that every message starts with either PUSH or POP so the server knows what to do with it. When the queue is empty the server sends back the string EMPTY so the broker knows to return None.

### What to do next:
Next I am going to work on task.py for the @task decorator.

## 2026-05-25

### What I worked on:
Today I wrote the Task class and the @task decorator. The Task class wraps a function and gives it a delay() method. When you call delay() it builds a message dict with a unique task id, the function name, and any args or kwargs, then enqueues it. I also wrote a configure() function so the task knows which broker to use.

### What I struggled with:
I struggled with finding a way to make the broker work for both Redis and the socket broker inside the task class. I also had trouble making delay() work for any function since different functions take different arguments.

### Decision I made:
I stored the function name as a string in the message instead of the actual function object because you cannot serialize a function. I also used *args and **kwargs so delay() works with any function signature.

### What to do next:
Next I am going to work on the worker pool.

## 2026-05-26

### What I worked on:
Today I wrote the WorkerPool class. It takes a broker and a number of workers and spins up that many threads. Each thread runs a loop that pulls messages off the queue, finds the function by name, runs it, and saves the result. I also added a stop event so the pool can shut down cleanly.

### What I struggled with:
I struggled with getting the actual function object from just its name. I originally used getattr by itself without first getting the module, so it didn't work. I also had trouble understanding how the stop event works and how to make threads finish their current task before stopping instead of just cutting them off.

### Decision I made:
I used sys.modules to get the module first and then getattr to get the function object off of it. I also used t.join() so each thread finishes whatever it is working on before the pool fully stops.

### What to do next:
Next I am going to work on result storing.

## 2026-05-27

### What I worked on:
Today I wrote the result store. I made an abstract base class with save_result and get_result, then wrote two implementations: one that stores results in Redis as a hash and one that stores them in a SQLite database file.

### What I struggled with:
I struggled with figuring out how to read back bytes from Redis since it returns keys and values as bytes not strings. Had to call .decode() on the keys and use json.loads on the value.

### Decision I made:
I built both a Redis and SQLite store so the project supports both. Redis is faster for short lived results and SQLite is better if you want results to survive a restart.

### What to do next:
Next I am going to work on retry logic.

## 2026-06-12

### What I worked on:
Today I wrote the retry logic. I wrote three functions: retry() which re-enqueues a failed message after a delay, should_dead_letter() which checks if a message has exceeded the max retry limit, and move_to_dead_letter() which moves it to a separate failed queue.

### What I struggled with:
I struggled with figuring out how to create a separate dead letter queue using the same broker. I ended up temporarily swapping the queue name on the broker to dead_letter, enqueueing the message, then swapping it back.

### Decision I made:
I added exponential backoff plus a small random jitter to the delay before each retry so workers don't all hammer the queue at the same time. I also added an attempt counter to the message so the system knows when to stop retrying.

### What to do next:
Next I am going to work on the dashboard and write examples.

## 2026-06-15

### What I worked on:
Today I wrote the dashboard and five example scripts. The dashboard uses the Rich library to show a live updating table of how many tasks are pending and how many are in the dead letter queue. The examples cover an ecommerce order pipeline with chained tasks, a retry and dead letter demo, a dashboard flood test, a GIL comparison between IO and CPU bound work, and an IO benchmark that plots sequential vs worker time on a chart.

### What I struggled with:
I struggled with making the dashboard loop work inside an example script without running forever. The dashboard's start() method runs an infinite loop which is fine for a real terminal monitor but breaks a script that needs to exit. I fixed it by using the make_table() method directly inside a bounded Rich Live block.

### Decision I made:
I decided to write examples that each demonstrate one specific reason to use a task queue, like keeping a web request fast, handling flaky external services, or showing the GIL limits on CPU bound threads. That way the examples are useful for explaining the project to someone else, not just testing that it works.

## 2026-07-28

### What I worked on:
Today I added a full test suite using pytest. I used Codex to generate the tests and then read through all of them to understand what they were doing. The suite covers all five core modules: the brokers, result stores, retry logic, task decorator, and worker pool. I also have a conftest.py that holds shared fixtures like a sample message and a mock broker so each test file does not have to set those up on its own.

The broker tests use fakeredis so they don't need a real Redis server running. The socket broker tests spin up the actual TCP server once for the whole session and reuse it. The retry tests use monkeypatch to skip the real sleep so they run fast. The worker tests use a fake result store and a fake broker that feeds one message and then sets the stop event so the worker loop exits cleanly.

### What I struggled with:
Reading through the tests helped me understand things I had not thought about when writing the code. For example the broker tests check that args come back as a list instead of a tuple because JSON does not have tuples, so when you deserialize a message the args come back as a list. I had not noticed that before.

The worker test that checks the thread count was tricky to read because it monkeypatches the Thread class itself with a fake one that just tracks whether start was called.

### Decision I made:
I used Codex to write the tests since test writing was not the main thing I was trying to learn on this project. But I made sure to read every test and understand what it was checking before moving on. Going forward I want to write tests myself so I get more practice with pytest fixtures and monkeypatching.

## 2026-08-27

### What I worked on:
Today I prepared the dashboard for deployment with Vercel for the frontend and Render for the API, worker, and Redis-compatible Key Value service.

I changed both `RedisBroker` and `RedisResultStore` to read a `REDIS_URL` environment variable and connect with `redis.Redis.from_url()`. They still default to `redis://localhost:6379`, so local development works without environment configuration.

I changed the React dashboard to read `VITE_API_URL`, with `http://localhost:8000` as the local fallback. Every frontend API request now uses that shared base URL instead of a hardcoded localhost address.

I also made the worker-burst demo safer for a small hosted Redis instance. Polling is now limited to one request cycle at a time, runs once per second instead of every 300 milliseconds, and retries on the next cycle when a request fails.

Finally, I changed the burst to use batch endpoints. The frontend submits all 30 demo tasks with one `POST /task/batch` request and polls their statuses with one `POST /tasks/results` request. The API now types batch tasks as `list[EnqueueRequest]` and provides `/tasks/results` to return a result for every requested task ID.

### What I struggled with:
The original burst demo made 30 task-result requests at once and repeated that work every 300 milliseconds. On Render's free Key Value instance, this created enough concurrent Redis connections to hit the service's client limit. The worker then failed to start even though the FastAPI server remained available, leaving queued tasks unprocessed.

### Decision I made:
I kept the existing single-task endpoints for the regular enqueue form and task-result feed, but used batch endpoints only for the fixed-size burst demonstration. This preserves the simple API while avoiding a connection spike during the visual concurrency demo.

### What to do next:
If the project grows beyond a demo, add authentication, restrict CORS to the deployed frontend domain, move the worker to its own always-running service, and use a persistent Redis-compatible datastore.
