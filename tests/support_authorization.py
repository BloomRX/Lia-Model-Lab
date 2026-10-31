"""Synthetic test grants ONLY. Not operator confirmation; no real checkpoint/authorization."""
import os
import secrets
import sqlite3
import time
from pathlib import Path
from lia_lab.io import canonical
from lia_lab.authorization import SCHEMA


def fixture_grant(path, operation, not_before=None, expires=None):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    grant_id = 'unit-fixture-' + secrets.token_hex(6)
    now = time.time()
    with sqlite3.connect(path) as db:
        db.execute(SCHEMA)
        db.execute('INSERT INTO grants VALUES (?, ?, ?, ?, NULL, NULL, NULL)',
            (grant_id, canonical(operation), now-1 if not_before is None else not_before,
             now+300 if expires is None else expires))
    os.chmod(path, 0o600)
    return path, grant_id
