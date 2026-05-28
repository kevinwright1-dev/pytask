## 2026-05-23

### What I worked on:

### What I struggled with:

### Decision I made:

### What to do next:

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
Today I worked on the 

### What I struggled with:

### Decision I made:

### What to do next: