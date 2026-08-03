import socket
import threading
from .base import Broker
import json

def broker_server():
    """Run a TCP queue server for environments without Redis.

    This server is intentionally minimal. Messages live only in memory, and the
    protocol is just PUSH/POP text commands. That makes it useful for local
    demos or learning how broker boundaries work without installing Redis.
    """

    queue = []


    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("", 9999)) 
    server.listen()

    while True:
        conn, addr = server.accept()
        data = conn.recv(4096)
        message = data.decode("utf-8") 

        if message.startswith("PUSH"):

            json_data = message[5:]
            queue.append(json_data)
            conn.sendall("OK".encode("utf-8"))

        elif message.startswith("POP"):

            if len(queue) > 0:
                task = queue.pop(0)
                conn.sendall(task.encode())
            else:
                conn.sendall("EMPTY".encode("utf-8"))

class SocketBroker(Broker):
    """Pure TCP broker client for the lightweight socket server."""

    def __init__(self, host="localhost", port=9999):

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))

    def enqueue(self, message):
        """Send one JSON task message to the socket server."""

        message_json = json.dumps(message)
        client_msg = "PUSH" + " " + message_json
        self.client.send(client_msg.encode())

    def dequeue(self, timeout):
        """Request one queued task from the socket server.

        The current socket server responds immediately instead of honoring a
        timeout, but the method keeps the Broker interface compatible with
        RedisBroker and WorkerPool.
        """
        self.client.send("POP".encode())
        data = self.client.recv(4096)
        message = data.decode("utf-8")
        if message == "EMPTY":
            return None
        else:
            return json.loads(message)

    def close(self):
        """Close the client socket."""
        self.client.close()

def start_server():
    """Start the demo socket server in a daemon background thread."""

    t = threading.Thread(target=broker_server)
    t.daemon = True
    t.start()
