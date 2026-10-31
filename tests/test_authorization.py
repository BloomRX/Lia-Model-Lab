"""All grants here are temporary synthetic fixture approvals, NOT owner authorization."""
import copy
import io
import os
from pathlib import Path
import sqlite3
import time
import pytest
from lia_lab.authorization import consume_grant, confirm_plan, check_store
from lia_lab.inference import make_operation, operation_from_plan
from lia_lab.io import LabError, atomic_json, load
from support_authorization import fixture_grant


@pytest.fixture
def operation(snapshot, tmp_path):
    return make_operation(*snapshot,'configs/inference-suite.json',tmp_path/'research',tmp_path/'approved','fixture-only')


def test_positive_atomic_single_use(operation,tmp_path):
    store,grant=fixture_grant(tmp_path/'operator/grants.db',operation)
    receipt=consume_grant(store,grant,operation)
    assert receipt['action']=='local-inference' and receipt['identity_authenticated'] is False
    with pytest.raises(LabError,match='consumed'):consume_grant(store,grant,operation)


@pytest.mark.parametrize('field', ['action','model_id','revision','snapshot_manifest_sha256','suite_sha256','source_snapshot_sha256','license','limits','arguments','disallowed_actions'])
def test_every_operation_binding(operation,tmp_path,field):
    store,grant=fixture_grant(tmp_path/'operator/grants.db',operation)
    modified=copy.deepcopy(operation)
    if field=='limits':modified[field]['max_requests']+=1
    elif field=='arguments':modified[field]['run_id']='other'
    else:modified[field]='different'
    with pytest.raises(LabError,match='match'):consume_grant(store,grant,modified)
    # A rejected mismatch does NOT consume the grant; exact operation remains valid.
    assert consume_grant(store,grant,operation)['single_use']


@pytest.mark.parametrize('bounds',[(-20,-10),(100,200),(-1,4000)])
def test_temporal_gates(operation,tmp_path,bounds):
    now=time.time()
    store,grant=fixture_grant(tmp_path/'operator/grants.db',operation,now+bounds[0],now+bounds[1])
    with pytest.raises(LabError,match='lifetime|valid|expired'):consume_grant(store,grant,operation)


def test_absent_invalid_and_forged_string(operation,tmp_path):
    with pytest.raises(LabError,match='missing'):consume_grant(tmp_path/'missing.db','APPROVED',operation)
    store=tmp_path/'operator.db';store.write_text('APPROVED');os.chmod(store,0o600)
    with pytest.raises(LabError,match='invalid'):consume_grant(store,'APPROVED',operation)
    store.unlink();store,grant=fixture_grant(store,operation)
    with pytest.raises(LabError,match='missing'):consume_grant(store,'arbitrary-reference',operation)


def test_store_outside_artifacts_and_permissions(operation,tmp_path):
    for base in [operation['snapshot'],operation['research_root'],operation['approved_root'],Path.cwd()]:
        with pytest.raises(LabError,match='outside'):check_store(Path(base)/'grants.db',operation,False)
    store,grant=fixture_grant(tmp_path/'operator/grants.db',operation)
    link=tmp_path/'link.db';link.symlink_to(store)
    with pytest.raises(LabError,match='symlink'):consume_grant(link,grant,operation)
    if os.name=='posix':
        os.chmod(store,0o644)
        with pytest.raises(LabError,match='owner-only'):consume_grant(store,grant,operation)


def test_noninteractive_never_confirms(operation,tmp_path,monkeypatch):
    monkeypatch.setattr('sys.stdin',io.StringIO('yes'))
    path=tmp_path/'plan.json';atomic_json(path,operation)
    with pytest.raises(LabError,match='interactive'):confirm_plan(path,tmp_path/'operator/grants.db')
    assert not (tmp_path/'operator').exists()


def test_interactive_decline_writes_nothing(operation,tmp_path,monkeypatch):
    class Terminal(io.StringIO):
        def isatty(self):return True
    monkeypatch.setattr('sys.stdin',Terminal());monkeypatch.setattr('sys.stdout',Terminal())
    monkeypatch.setattr('builtins.input',lambda _: 'no')
    path=tmp_path/'plan.json';atomic_json(path,operation)
    with pytest.raises(LabError,match='declined'):confirm_plan(path,tmp_path/'operator/grants.db')
    assert not (tmp_path/'operator').exists()


def test_confirm_fixture_terminal_only(operation,tmp_path,monkeypatch):
    # Fake operator + synthetic model + temp store, solely to test interactive control flow.
    class Terminal(io.StringIO):
        def isatty(self):return True
    monkeypatch.setattr('sys.stdin',Terminal());monkeypatch.setattr('sys.stdout',Terminal())
    def confirmation(prompt):return prompt.split('Type: ')[1].strip()
    monkeypatch.setattr('builtins.input',confirmation)
    plan=tmp_path/'fixture-plan.json';atomic_json(plan,operation)
    result=confirm_plan(plan,tmp_path/'fixture-operator/grants.db',60)
    assert not result['identity_authenticated']
    assert consume_grant(result['store'],result['approval_id'],operation)['single_use']


def test_plan_staleness(operation,snapshot):
    assert operation_from_plan(operation)==operation
    (snapshot[0]/'LICENSE').write_text('changed synthetic license')
    with pytest.raises(LabError):operation_from_plan(operation)


def test_concurrent_claim_only_one_wins(operation,tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    store,grant=fixture_grant(tmp_path/'operator/grants.db',operation)
    def claim(_):
        try:consume_grant(store,grant,operation);return True
        except LabError:return False
    with ThreadPoolExecutor(max_workers=2) as pool:assert sum(pool.map(claim,range(2)))==1


def test_worker_claim_and_finalization_are_not_replayable(operation,tmp_path):
    from lia_lab.authorization import claim_worker,finalize_grant
    store,grant=fixture_grant(tmp_path/'operator/grants.db',operation)
    with pytest.raises(LabError):claim_worker(store,grant,operation)  # no supervisor claim yet
    consume_grant(store,grant,operation)
    claim_worker(store,grant,operation)
    with pytest.raises(LabError):claim_worker(store,grant,operation)
    finalize_grant(store,grant,operation)
    with pytest.raises(LabError):claim_worker(store,grant,operation)


def test_blocked_grant_finalized_even_without_worker(operation,tmp_path):
    from lia_lab.authorization import finalize_grant,claim_worker
    store,grant=fixture_grant(tmp_path/'operator/grants.db',operation)
    consume_grant(store,grant,operation);finalize_grant(store,grant,operation)
    with pytest.raises(LabError):claim_worker(store,grant,operation)


def test_finalization_bound_to_consumed_operation_and_idempotent(operation,tmp_path):
    import sqlite3
    import copy
    from lia_lab.authorization import finalize_grant
    store,grant=fixture_grant(tmp_path/'operator/finalize.db',operation)
    with pytest.raises(LabError):finalize_grant(store,grant,operation)
    consume_grant(store,grant,operation)
    altered=copy.deepcopy(operation);altered['revision']='f'*40
    with pytest.raises(LabError):finalize_grant(store,grant,altered)
    finalize_grant(store,grant,operation)
    with sqlite3.connect(store) as db:
        first=db.execute('SELECT finished FROM grants WHERE id=?',(grant,)).fetchone()[0]
    finalize_grant(store,grant,operation)
    with sqlite3.connect(store) as db:
        assert db.execute('SELECT finished FROM grants WHERE id=?',(grant,)).fetchone()[0]==first
