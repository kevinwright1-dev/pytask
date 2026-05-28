from abc import ABC, abstractmethod
import redis
import sqlite3

class ResultStore(ABC):
    @abstractmethod
    def save_result(self, task_id, status, value):
        ...
    @abstractmethod
    def get_result(self, task_id):
        ...

class RedisResultStore(ResultStore):
    def __init__(self, host="localhost", port=6379):
        self.r = redis.Redis(host=host, port=port)
    def save_result(self, task_id, status, value):
        self.r.hset(task_id, mapping={"status": status, "value": value})
    def get_result(self, task_id):
        result = self.r.hgetall(task_id)
        if not result:
            return None
        return result

class SQLiteResultStore(ResultStore):
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
        sql = "INSERT OR REPLACE INTO tasks(task_id, status, value) VALUES(?,?,?)"
        self.cursor.execute(sql,(task_id, status, value))
        self.conn.commit()
    def get_result(self, task_id):
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

        
        