import json
import os

firebase_app = None


def firebase():
    global firebase_app
    if firebase_app is None:
        import firebase_admin
        from firebase_admin import credentials
        raw = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
        cred = credentials.Certificate(json.loads(raw)) if raw else credentials.ApplicationDefault()
        firebase_app = firebase_admin.initialize_app(cred, {
            'databaseURL': os.environ['FIREBASE_DATABASE_URL'],
            'storageBucket': os.environ['FIREBASE_STORAGE_BUCKET'],
        })
    return firebase_app

