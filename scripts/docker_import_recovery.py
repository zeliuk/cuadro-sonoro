"""Deterministic, synthetic Docker walkthrough for durable import recovery."""
import json
import sys
import time

from backend.identity import frame_key_for
from backend.lifecycle import recover_interrupted_jobs
from backend.state import store

FRAME_ID = 'docker-recovery-demo'
FRAME_KEY = frame_key_for(FRAME_ID)
JOB_ID = 'docker-recovery-job'


def main(command):
    if command == 'seed':
        job = {
            'id': JOB_ID, 'slot': 0, 'source_id': 'BaW_jenozKc', 'title': 'Importación sintética',
            'artist': 'Prueba local', 'status': 'uploading', 'percent': 42,
            'message': 'Subida interrumpida para la prueba Docker', 'created_at': time.time(),
            'execution_id': 'simulated-lost-process',
        }
        store.mutate(FRAME_KEY, lambda state: state['jobs'].update({JOB_ID: job}))
    elif command == 'recover':
        recover_interrupted_jobs()
    elif command == 'show':
        data = store.read(FRAME_KEY)
        print(json.dumps({'frame_id': FRAME_ID, 'job': data['jobs'].get(JOB_ID)}, ensure_ascii=False))
        return
    else:
        raise SystemExit('Uso: docker_import_recovery.py seed|recover|show')
    main('show')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) == 2 else '')
