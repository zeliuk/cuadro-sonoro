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
            # Keep the legacy single-collection `state` table inert; it has no
            # trustworthy frame identity and must never be assigned to a token.
            self.conn.execute('CREATE TABLE IF NOT EXISTS frame_states (frame_key TEXT PRIMARY KEY, data TEXT)')
            self.conn.commit()

    @staticmethod
    def _normalize(data):
        data = data or {}
        data.setdefault('slots', {})
        data.setdefault('jobs', {})
        return data

    def read(self, frame_key):
        if self.cloud:
            from firebase_admin import db
            data = db.reference(f'frames/{frame_key}', app=firebase()).get()
        else:
            row = self.conn.execute('SELECT data FROM frame_states WHERE frame_key=?', (frame_key,)).fetchone()
            data = json.loads(row[0]) if row else None
        return self._normalize(data)

    def read_all(self):
        if self.cloud:
            from firebase_admin import db
            frames = db.reference('frames', app=firebase()).get() or {}
            return {key: self._normalize(value) for key, value in frames.items()}
        rows = self.conn.execute('SELECT frame_key, data FROM frame_states').fetchall()
        return {key: self._normalize(json.loads(data)) for key, data in rows}

    def mutate(self, frame_key, fn):
        with lock:
            if self.cloud:
                from firebase_admin import db
                def update(state):
                    state = self._normalize(state)
                    fn(state)
                    return state
                return db.reference(f'frames/{frame_key}', app=firebase()).transaction(update)
            state = self.read(frame_key)
            fn(state)
            self.conn.execute('INSERT OR REPLACE INTO frame_states VALUES (?,?)', (frame_key, json.dumps(state)))
            self.conn.commit()
            return state

    def mutate_all(self, fn):
        for frame_key in self.read_all():
            self.mutate(frame_key, fn)


store = StateStore()

def patch_job(frame_key, job_id, **values):
    def apply(state):
        if job_id in state['jobs']:
            state['jobs'][job_id].update(values, updated_at=time.time())
    store.mutate(frame_key, apply)


def check_cancel(job_id):
    if job_id in cancelled:
        raise RuntimeError('Importación cancelada.')

