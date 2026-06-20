"""
Firebase Realtime Database initialization and utilities.
This module replaces Deta as the primary data storage backend.
"""

import firebase_admin
from firebase_admin import credentials, db
from os import getenv
import json
from typing import Any, Dict, List, Optional

# Initialize Firebase (credentials from environment or file)
def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Try environment variable (Render-friendly: paste entire JSON into one var)
        firebase_creds_json = getenv("FIREBASE_KEY_JSON") or getenv("FIREBASE_CREDENTIALS_JSON")
        if firebase_creds_json:
            creds_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(creds_dict)
        else:
            # Fall back to local file path
            firebase_creds_path = getenv("FIREBASE_CREDENTIALS_PATH", "firebase-key.json")
            cred = credentials.Certificate(firebase_creds_path)
        
        database_url = getenv("FIREBASE_DATABASE_URL")
        if not database_url:
            raise ValueError("FIREBASE_DATABASE_URL environment variable not set")
        
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
        
        return db.reference()
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        raise


# Get or initialize Firebase reference
_firebase_db = None

def get_firebase_ref():
    """Get Firebase Realtime Database reference"""
    global _firebase_db
    if _firebase_db is None:
        init_firebase()
        _firebase_db = db.reference()
    return _firebase_db


# Database reference functions (mimicking the old Deta API)

def client_ref():
    """Get reference to client database"""
    return db.reference('/client')


def notification_ref():
    """Get reference to notification database"""
    return db.reference('/notification')


def command_ref():
    """Get reference to command database"""
    return db.reference('/command')


def auth_ref():
    """Get reference to auth database"""
    return db.reference('/auth')


# Utility functions to match Deta API

class FirebaseWrapper:
    """Wrapper to provide Deta-like interface for Firebase"""
    
    def __init__(self, path: str):
        self.path = path
        self.ref = db.reference(path)
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a single record by key"""
        data = self.ref.child(key).get()
        if data is None:
            return None
        if data:
            data['key'] = key
        return data
    
    def put(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Add a new record (auto-generates key) and return it"""
        key = self.ref.push(data).key
        return {'key': key, **data}
    
    def update(self, key: str, updates: Dict[str, Any]):
        """Update an existing record"""
        self.ref.child(key).update(updates)
        return True
    
    def delete(self, key: str):
        """Delete a record"""
        self.ref.child(key).delete()
        return True
    
    def fetch(self) -> 'FetchResult':
        """Fetch all records and return as FetchResult object"""
        data = self.ref.get()
        if data is None:
            data = {}
        items = []
        for key, value in data.items():
            if isinstance(value, dict):
                value['key'] = key
                items.append(value)
        return FetchResult(items)


class FetchResult:
    """Mimic Deta's fetch result"""
    
    def __init__(self, items: List[Dict[str, Any]]):
        self.items = items
    
    def __len__(self):
        return len(self.items)


# Export wrapper functions
def client_db_wrapper():
    """Get client database wrapper"""
    return FirebaseWrapper('/client')


def notification_db_wrapper():
    """Get notification database wrapper"""
    return FirebaseWrapper('/notification')


def command_db_wrapper():
    """Get command database wrapper"""
    return FirebaseWrapper('/command')


def auth_db_wrapper():
    """Get auth database wrapper"""
    return FirebaseWrapper('/auth')
