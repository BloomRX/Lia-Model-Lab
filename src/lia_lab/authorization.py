"""Operator-confirmed, single-use local grants. NOT identity authentication or a sandbox."""
import os
from pathlib import Path
import secrets
import sqlite3
import stat
import sys
import time
import math
import json
from .io import LabError, canonical, json_loads, load

SCHEMA = "CREATE TABLE IF NOT EXISTS grants (id TEXT PRIMARY KEY, operation TEXT NOT NULL, not_before REAL NOT NULL, expires REAL NOT NULL, consumed REAL, worker_started REAL, finished REAL)"


def check_store(path, operation, existing=True):
    path = Path(path).absolute()
    if path.is_symlink() or path.parent.is_symlink():
        raise LabError('approval store cannot be a symlink')
    path = path.resolve()
    forbidden = [Path(__file__).resolve().parents[2], *(Path(operation[k]) for k in
                 ('snapshot', 'research_root', 'approved_root', 'repository_root'))]
    if any(path.is_relative_to(p.resolve()) for p in forbidden):
        raise LabError('operator store must be outside repository/snapshot/research/approved artifacts')
    if existing and not path.is_file():
        raise LabError('external operator approval store missing')
    if path.exists() and os.name == 'posix':
        info = path.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise LabError('operator store must be owner-only (0600) and owned by current OS user')
    return path


def confirm_plan(plan_path, store, ttl=900):
    """Only interactive operator CLI calls this. No --yes/noninteractive grant creation."""
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise LabError('approval creation requires an interactive operator terminal; strings/--yes are not authorization')
    if type(ttl) is not int or not 1 <= ttl <= 3600:
        raise LabError('approval lifetime must be 1..3600 seconds')
    from .inference import operation_from_plan
    operation = operation_from_plan(load(plan_path))  # revalidate the exact displayed inputs
    store = check_store(store, operation, existing=False)
    import hashlib
    operation_hash = hashlib.sha256(canonical(operation).encode()).hexdigest()
    print('LOCAL INFERENCE ONLY. No download, training, publishing or release. No external charges allowed.')
    print(json.dumps(operation, ensure_ascii=False, indent=2, allow_nan=False))
    print(f"Grant valid for {ttl} seconds from confirmation; single use, including failed/blocked attempts.")
    print('This is an operational confirmation, NOT cryptographic proof of the owner identity.')
    phrase = 'ALLOW LOCAL INFERENCE ' + operation_hash
    if input('Review the exact model/license/hashes/budgets. Type: ' + phrase + '\n') != phrase:
        raise LabError('operator declined; no grant created')
    store.parent.mkdir(parents=True, exist_ok=True)
    if not store.exists():
        fd = os.open(store, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
    check_store(store, operation)
    grant_id = secrets.token_hex(16)
    now = time.time()
    try:
        with sqlite3.connect(store) as db:
            db.execute(SCHEMA)
            db.execute('INSERT INTO grants VALUES (?, ?, ?, ?, NULL, NULL, NULL)', (grant_id, canonical(operation), now, now + ttl))
    except sqlite3.Error as exc:
        raise LabError('operator store schema/write failed; no new grant confirmed') from exc
    return {'approval_id': grant_id, 'store': str(store), 'expires_unix': now + ttl,
            'identity_authenticated': False, 'single_use': True}


def consume_grant(store, grant_id, operation):
    """Atomic claim before model execution. Failure/crash burns grant; never refunds it."""
    path = check_store(store, operation)
    try:
        with sqlite3.connect(path.as_uri() + '?mode=rw', uri=True, timeout=5) as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT operation, not_before, expires, consumed FROM grants WHERE id=?', (grant_id,)).fetchone()
            now = time.time()
            if row is None or row[3] is not None:
                raise LabError('approval missing or already consumed')
            if (any(type(v) not in (int,float) or not math.isfinite(v) for v in row[1:3]) or
                    not row[1] <= now < row[2] or row[2] - row[1] > 3600):
                raise LabError('approval expired/not-yet-valid/invalid lifetime')
            if json_loads(row[0]) != operation or canonical(json_loads(row[0])) != canonical(operation):
                raise LabError('approval does not match exact operation/checkpoint/manifest/budgets')
            db.execute('UPDATE grants SET consumed=? WHERE id=? AND consumed IS NULL', (now, grant_id))
        return {'approval_id': grant_id, 'consumed_at_unix': now, 'expires_unix': row[2],
                'identity_authenticated': False, 'store_permission_check': 'posix-owner-only' if os.name == 'posix' else 'not-applied-platform',
                'action': 'local-inference', 'single_use': True}
    except sqlite3.Error as exc:
        raise LabError('invalid/unavailable operator approval store') from exc


def claim_worker(store, grant_id, operation):
    """Private worker still checks the external grant; env flags are NEVER authorization."""
    path = check_store(store, operation)
    try:
        with sqlite3.connect(path.as_uri() + '?mode=rw', uri=True, timeout=5) as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT operation, not_before, expires, consumed, worker_started, finished FROM grants WHERE id=?', (grant_id,)).fetchone()
            now = time.time()
            if (row is None or row[3] is None or row[4] is not None or row[5] is not None or
                    not row[1] <= row[3] <= now < row[2] or canonical(json_loads(row[0])) != canonical(operation)):
                raise LabError('worker grant absent/unclaimed/replayed/expired/finalized/mismatched')
            if now - row[3] >= operation['limits']['max_duration_seconds']:
                raise LabError('worker operation deadline expired')
            db.execute('UPDATE grants SET worker_started=? WHERE id=?', (now, grant_id))
    except sqlite3.Error as exc:
        raise LabError('worker operator-store validation failed') from exc


def finalize_grant(store, grant_id, operation):
    path = check_store(store, operation)
    try:
        with sqlite3.connect(path.as_uri() + '?mode=rw', uri=True) as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT operation, consumed, finished FROM grants WHERE id=?', (grant_id,)).fetchone()
            if row is None or row[1] is None or canonical(json_loads(row[0])) != canonical(operation):
                raise LabError('cannot finalize absent/unconsumed/mismatched grant')
            if row[2] is None:
                db.execute('UPDATE grants SET finished=? WHERE id=?', (time.time(), grant_id))
            # Repeated finalization of the same operation preserves the first audit time.
    except sqlite3.Error as exc:
        raise LabError('cannot finalize operator audit record') from exc
