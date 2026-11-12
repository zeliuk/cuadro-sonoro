import json
import os
import sqlite3
import threading
import time

from .firebase_client import firebase

lock = threading.RLock()
cancelled: set[str] = set()


class StateStore:
    """RTDB in deployment; SQLite only for local development/tests."""
    def __init__(self):
        self.cloud = bool(os.getenv('FIREBASE_DATABASE_URL'))
        self.conn = None
        if not self.cloud:
            self.conn = sqlite3.connect(os.getenv('STATE_DB', '/tmp/sonoro.sqlite3'), check_same_thread=False)
            self.conn.execute('CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, data TEXT)')
            self.conn.commit()

    def read(self):
        if self.cloud:
            from firebase_admin import db
            data = db.reference('prototypes/sonoro', app=firebase()).get()
        else:
            row = self.conn.execute('SELECT data FROM state WHERE id=1').fetchone()
            data = json.loads(row[0]) if row else None
        data = data or {}
        data.setdefault('slots', {})
        data.setdefault('jobs', {})
        return data

    def mutate(self, fn):
        with lock:
            if self.cloud:
                from firebase_admin import db
                def update(state):
                    state = state or {'slots': {}, 'jobs': {}}
                    state.setdefault('slots', {})
                    state.setdefault('jobs', {})
                    fn(state)
                    return state
                return db.reference('prototypes/sonoro', app=firebase()).transaction(update)
            state = self.read()
            fn(state)
            self.conn.execute('INSERT OR REPLACE INTO state VALUES (1,?)', (json.dumps(state),))
            self.conn.commit()
            return state


store = StateStore()

def patch_job(job_id, **values):
    def apply(state):
        if job_id in state['jobs']:
            state['jobs'][job_id].update(values, updated_at=time.time())
    store.mutate(apply)


def check_cancel(job_id):
    if job_id in cancelled:
        raise RuntimeError('Importación cancelada.')

