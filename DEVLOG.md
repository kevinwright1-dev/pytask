## 2026-05-25

### What I worked on:
Today I worked on the Broker for Redis. I had to install redis on my computer. I wrote the enqueue, dequeue, and close jsut like the abstract class I made before. I also used json to seralize the message so it can be read by redis.

### What I struggled with:
I learned the difference between json.dump and json.dumps. Json.dump is used for writting onto a Json file, while json.dumps is used to turn a Python object into a Json formatted string. I got that confused when trying to seralize the message so that redis can read it. 

When I was putting in the parameters for lpush and brpop I used a hardcoded string "queue_name" instead of the actually variable self.queue_name.

I tried to put __init__ outside of the class. I thought init was a function when it was a constructor


### Decision I made:
I decided to serialize the message using Json so that redis would be able to read the message. 


### What to do next:
Next im going to work on the socket broker.

## 2026-05-23

### What I worked on:
Today I worked on the the socket broker and creating a server to hold a queue. The server holds the queue as a plain python list and connects to workers and producers. I also wrote the socket broker as a class called SocketBroker that is very similar to the redis broker class except it uses the tcp socket server I created to store and return messages. 

### What I struggled with:
Originally I used port 999 because I didnt know that ports lower than 1024 are reserved for os, so I changed it to 9999. Also I didnt send a meessage back to the client when the server recieved a push command, so I changed it that sends an ok message after pushing the message onto the queue. I accidently sent push instead of pop for dequeue in the socket broker. 
### Decision I made:
I decided that each meessage for task will start with either push or pop to decided wether to dequeue or enqueue. I also decided that when the queue is empty the server sends back the string "EMPTY" to the client
### What to do next:
Next im going to work on the task.py for the @task decorator
## 2026-05-24

### What I worked on:
Today I worked on the Task class and the task decorator. The task class builds the message for the broker to use. It takes in the function object. The class has one method that creates the message dict by generating the task id using uuid, the function name using __name__ on the function objects name, and getting args and kwargs but setting them as arguements for the method. After the message dict is created it is then enqueued. To enqueue I needed to create a broker object on configure it so the task class new which broker object to use. I also wrote the task wrapper function so that when the function task is called it creates the Task object using the function from the arguement.
### What I struggled with:
I struggled with finding a way to configure the broker object so that it works for both Redis broker and the Socket broker. I also struggled with finding a way for the task class method to work for any type of function

### Decision I made:
I decided to store the function object as a string in the message instead of a function object because you cant serialize a function object. I also decided to take in args and kwargs for the task method because I need the method to work on any type of function 
### What to do next:
Next I am going to work the worker pool
## 2026-05-25

### What I worked on:
Today I worked on the worker pool. I created the class for the workers called worker pool with a constructor that takes a broker object and number of workers. Inside the constructor we have a list of threads that the workers can run on and a stop event for when we want the workers to stop running. The class has a three methods, start, run, and stop. The start method creates a thread for each worker, starts the thread, then appends them to the thread queue. The run method dequeues a message and takes the arg and/or kwarg and runs the function. The stop method sets the stop event for the threads.
### What I struggled with:
I struggled with understanding how to get the function object so that I can run the actually function. I orginally just used the getattr without getting the module. I also struggled with understanding how to use the stop_event correctly. 

### Decision I made:
I decided to use the sys.modules function to find the module for the function in the method. I also decided to use getattr to get the actually function object. I also decided that instead of just stoping all the threads when the stop event is set, I would let them finish their task using t.join()

### What to do next:
Next I am going to work on result storing

## 2026-05-23

### What I worked on:
Today I worked on the result storing. I wrote the abstract class for how I wanted results to be stored and returned with methods save_results and get_results. I chose to store reuslt in a Redis server and a SQLLite file. In Redis 
### What I struggled with:


### Decision I made:

### What to do next:
## 2026-06-12

### What I worked on:
Today I worked on the retry logic for the broker system. I wrote three functions, one to retry a task, one to check to see if a task should be moved to the failed task queue, and one that adds the task to the failed task queue. 
### What I struggled with:
I struggled with understanding how to create a new queue in the broker list for the failed task.

### Decision I made:
I decided to add a delay before each retry so the workers will not continuously retry task. I also added an attempt amount to decided when worker should stop retrying a task.

### What to do next:

