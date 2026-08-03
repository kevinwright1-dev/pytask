from abc import ABC, abstractmethod
import json
import redis
import sqlite3

class ResultStore(ABC):
    """Common interface for storing task outcomes.

    Brokers move work around; result stores answer the follow-up question:
    "What happened to task id X?" Keeping this interface separate lets pytask
    support different storage backends without changing task execution.
    """

    @abstractmethod
    def save_result(self, task_id, status, value):
        """Persist one task's final status and return value."""
        ...

    @abstractmethod
    def get_result(self, task_id):
        """Return a saved result dict, or None when no result exists yet."""
        ...

class RedisResultStore(ResultStore):
    """Store task results in Redis hashes keyed by task id."""

    def __init__(self, host="localhost", port=6379):

        self.r = redis.Redis(host=host, port=port)

    def save_result(self, task_id, status, value):
        """Save a result payload that can later be fetched by task id."""

        self.r.hset(task_id, mapping={"status": status, "value": json.dumps(value)})

    def get_result(self, task_id):
        """Load and decode one Redis result hash."""

        result = self.r.hgetall(task_id)
        if not result:
            return None
        return {
            "status": result[b"status"].decode(),
            "value": json.loads(result[b"value"])
        }

class SQLiteResultStore(ResultStore):
    """Store task results in a local SQLite database.

    SQLite is useful for local development, demos, or single-machine apps where
    bringing up Redis just to keep result history would be unnecessary.
    """

    def __init__(self):

        self.conn = sqlite3.connect("results.db")
        statement = """CREATE TABLE IF NOT EXISTS tasks (
                        task_id text PRIMARY KEY,
                        status text NOT NULL,
                        value text
                    );"""
        self.cursor = self.conn.cursor()
        self.cursor.execute(statement)

    def save_result(self, task_id, status, value):
        """Insert or update the result for a task id."""

        sql = "INSERT OR REPLACE INTO tasks(task_id, status, value) VALUES(?,?,?)"
        self.cursor.execute(sql,(task_id, status, value))
        self.conn.commit()

    def get_result(self, task_id):
        """Fetch one SQLite result row and normalize it to a dict."""

        sql = "SELECT * FROM tasks WHERE task_id = ?"
        self.cursor.execute(sql, (task_id,))
        row = self.cursor.fetchone()
        if row is None:
            return None
        return {
            "task_id": row[0],
            "status": row[1],
            "value": row[2]
        }
