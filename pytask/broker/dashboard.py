import time
import redis
from rich.live import Live
from rich.table import Table


class Dashboard():
    def __init__(self, broker, host="localhost", port=6379):
        self.r = redis.Redis(host=host, port=port)
        self.broker = broker
    def make_table(self):
        table = Table(title="pytask dashboard")
        table.add_column("Queue")
        table.add_column("Pending Tasks")
        table.add_row("default",str(self.r.llen("default")))
        table.add_row("dead_letter", str(self.r.llen("dead_letter"))) 
        return table
    def start(self):
        with Live(self.make_table(), refresh_per_second=1) as live:
            while True:
                live.update(self.make_table())
                time.sleep(1)
