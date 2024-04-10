import os

import redis


class DB:
    def __init__(self):
        host = os.environ.get("REDIS_DB", "localhost")
        self.con = redis.Redis(host=host, port=6379)

    def save(self, key: str, value: dict):
        self.con.set(key, str(value))
        # print(f"Saving data - {key}:{value}")

    def get_all(self):
        for key in self.con.scan_iter('????????-????-*'):
            # scan_iter использует паттерн ^^^^^, чтобы получать только определенные записи с ключом record_id
            # без паттерна он будет также доставать таски Celery
            yield key, self.con.get(key)


db = DB()
