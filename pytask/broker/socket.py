import socket
import threading
from .base import Broker
import json
def broker_server():
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

    def __init__(self, host="localhost", port=9999):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
    def enqueue(self, message):
        message_json = json.dumps(message)
        client_msg = "PUSH" + " " + message_json
        self.client.send(client_msg.encode())
    def dequeue(self, timeout):
        self.client.send("POP".encode())
        data = self.client.recv(4096)
        message = data.decode("utf-8")
        if message == "EMPTY":
            return None
        else:
            return json.loads(message)
    def close(self):
        self.client.close()

def start_server():
    t = threading.Thread(target=broker_server)
    t.daemon = True
    t.start()

    
        