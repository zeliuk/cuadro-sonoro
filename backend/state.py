import json
import os
import sqlite3
import threading
import time
import uuid

from .firebase_client import firebase

lock = threading.RLock()


class StateStore:
    """RTDB in deployment; durable SQLite for local single-worker operation."""
    def __init__(self):
        self.cloud = bool(os.getenv('FIREBASE_DATABASE_URL'))
        self.conn = None
        if not self.cloud:
            database = os.getenv('STATE_DB', '/tmp/sonoro.sqlite3')
            os.makedirs(os.path.dirname(os.path.abspath(database)), exist_ok=True)
            self.conn = sqlite3.connect(database, check_same_thread=False, timeout=30)
            self.conn.execute('PRAGMA journal_mode=WAL')
            self.conn.execute('PRAGMA busy_timeout=30000')
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
            with lock:
                row = self.conn.execute('SELECT data FROM frame_states WHERE frame_key=?', (frame_key,)).fetchone()
            data = json.loads(row[0]) if row else None
        return self._normalize(data)

    def ensure(self, frame_key):
        if self.cloud:
            from firebase_admin import db
            reference = db.reference(f'frames/{frame_key}', app=firebase())
            return self._normalize(reference.transaction(lambda current: self._normalize(current)))
        with lock:
            self.conn.execute('INSERT OR IGNORE INTO frame_states VALUES (?, ?)', (frame_key, json.dumps({'slots': {}, 'jobs': {}})))
            self.conn.commit()
            return self.read(frame_key)

    def read_all(self):
        if self.cloud:
            from firebase_admin import db
            frames = db.reference('frames', app=firebase()).get() or {}
            return {key: self._normalize(value) for key, value in frames.items()}
        with lock:
            rows = self.conn.execute('SELECT frame_key, data FROM frame_states').fetchall()
        return {key: self._normalize(json.loads(data)) for key, data in rows}

    def mutate(self, frame_key, fn):
        if self.cloud:
            from firebase_admin import db
            def update(state):
                state = self._normalize(state)
                fn(state)
                return state
            return db.reference(f'frames/{frame_key}', app=firebase()).transaction(update)
        # BEGIN IMMEDIATE serializes read/modify/write across independent API processes.
        with lock:
            self.conn.execute('BEGIN IMMEDIATE')
            try:
                row = self.conn.execute('SELECT data FROM frame_states WHERE frame_key=?', (frame_key,)).fetchone()
                state = self._normalize(json.loads(row[0]) if row else None)
                fn(state)
                self.conn.execute('INSERT OR REPLACE INTO frame_states VALUES (?,?)', (frame_key, json.dumps(state)))
                self.conn.commit()
                return state
            except BaseException:
                self.conn.rollback()
                raise

    def mutate_all(self, fn):
        for frame_key in self.read_all():
            self.mutate(frame_key, fn)


store = StateStore()


def patch_job(frame_key, job_id, execution_id=None, **values):
    """Progress is accepted only from the current execution and never past terminal state."""
    changed = False
    def apply(state):
        nonlocal changed
        job = state['jobs'].get(job_id)
        if not job or job.get('status') not in {'queued', 'downloading', 'processing', 'uploading'}:
            return
        if execution_id is not None and job.get('execution_id') != execution_id:
            return
        job.update(values, updated_at=time.time())
        changed = True
    store.mutate(frame_key, apply)
    return changed


def begin_execution(frame_key, job_id):
    run_id = uuid.uuid4().hex
    result = {'job': None}
    def claim(state):
        job = state['jobs'].get(job_id)
        if job and job.get('status') == 'queued':
            job.update(status='downloading', execution_id=run_id, percent=None,
                       attempts=job.get('attempts', 0) + 1,
                       message='Conectando con la fuente', updated_at=time.time())
            result['job'] = dict(job)
    store.mutate(frame_key, claim)
    return result['job']


def check_cancel(frame_key, job_id, execution_id):
    job = store.read(frame_key)['jobs'].get(job_id)
    if not job or job.get('status') not in {'queued', 'downloading', 'processing', 'uploading'} or job.get('execution_id') != execution_id:
        raise RuntimeError('Ejecución de importación cancelada o sustituida.')
