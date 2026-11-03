"""R1/R3/R4/R5 synthetic regressions; no runtime/model/license approval."""
from support_environment import synthetic_ram
import importlib.util
import os
import socket
from pathlib import Path
import pytest
from lia_lab.environment import memory, _v2_location
from lia_lab.datasets import read_examples
from lia_lab.training_prep import validate_tool_arguments, validate_tool_schema
from lia_lab.inference_protocol import validate_suite
from lia_lab.io import LabError, canonical, load
from test_foundation import example


def module(name):
    spec = importlib.util.spec_from_file_location(name, Path('scripts') / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def cgroup(tmp_path, member='/child', mount_root='/', limits=None):
    if os.name != 'posix':
        pytest.skip('Linux mountinfo fixtures require POSIX absolute path semantics')
    proc, mount = tmp_path / 'proc', tmp_path / 'mount'
    (proc / 'self').mkdir(parents=True)
    mount.mkdir()
    (proc / 'meminfo').write_text('MemTotal: 8388608 kB\nMemAvailable: 8388608 kB\n')
    (proc / 'self/cgroup').write_text('0::' + member + '\n')
    (proc / 'self/mountinfo').write_text(f'42 1 0:1 {mount_root} {mount} rw - cgroup2 cgroup rw\n')
    (mount / 'cgroup.controllers').write_text('memory cpu')
    for name, (maximum, used) in (limits or {'/': ('max', 0), '/child': (64*1024**2, 60*1024**2)}).items():
        node = mount / name.lstrip('/')
        node.mkdir(parents=True, exist_ok=True)
        if node != mount or maximum != 'max':
            (node / 'memory.max').write_text(str(maximum))
        (node / 'memory.current').write_text(str(used))
    return proc, mount


def test_r1_exact_8gib_child_64mib_used60(tmp_path):
    proc, _ = cgroup(tmp_path)
    assert memory(proc) == {'total_bytes': 64*1024**2, 'available_bytes': 4*1024**2}


@pytest.mark.parametrize('limits,total,available', [
    ({'/': (100, 90), '/child': (200, 100)}, 100, 10),
    ({'/': (200, 100), '/child': (100, 90)}, 100, 10),
    ({'/': ('max', 0), '/child': ('max', 999)}, 8*1024**3, 8*1024**3),
    ({'/': (100, 90), '/child': ('max', 1000)}, 100, 10),
])
def test_r1_each_ancestor_headroom(tmp_path, limits, total, available):
    proc, _ = cgroup(tmp_path, member='/a/b', limits={'/':('max',0), '/a':limits['/'], '/a/b':limits['/child']})
    assert memory(proc) == {'total_bytes': total, 'available_bytes': available}


def test_r1_three_levels_and_root_process(tmp_path):
    proc, mount = cgroup(tmp_path, member='/a/b', limits={'/': ('max', 0), '/a': (100, 95), '/a/b': (80, 20)})
    assert memory(proc)['available_bytes'] == 5
    (proc / 'self/cgroup').write_text('0::/\n')
    assert memory(proc)['available_bytes'] == 8*1024**3
    (mount / 'memory.max').unlink(missing_ok=True)  # actual Linux hierarchy root has no memory.max
    assert memory(proc)['available_bytes'] == 8*1024**3


@pytest.mark.parametrize('maximum,used', [('broken',0),('-1',0),(10,11),(10,-1),('max','NaN')])
def test_r1_invalid_values_unknown(tmp_path, maximum, used):
    proc, _ = cgroup(tmp_path, limits={'/': ('max',0), '/child':(maximum,used)})
    assert memory(proc) == {'total_bytes':None,'available_bytes':None}


@pytest.mark.parametrize('membership', ['', '0::/../child\n', '5:memory:/child\n', '0::/child\n5:cpu:/child\n'])
def test_r1_unknown_or_absent_membership(tmp_path, membership):
    proc, _ = cgroup(tmp_path)
    (proc/'self/cgroup').write_text(membership)
    assert memory(proc)['available_bytes'] is None


def test_r1_mount_root_mapping_but_hidden_ancestors_unknown(tmp_path):
    proc, mount = cgroup(tmp_path, member='/tenant/child', mount_root='/tenant')
    assert _v2_location(proc) == (Path('/tenant'), mount, mount/'child')
    assert memory(proc)['available_bytes'] is None


def test_r1_missing_leaf_or_unknown_mount(tmp_path):
    proc, mount = cgroup(tmp_path)
    (mount/'child/memory.current').unlink()
    assert memory(proc)['available_bytes'] is None
    (proc/'self/mountinfo').write_text('')
    assert memory(proc)['available_bytes'] is None


def test_r3_fifo_exact_scenario_no_writer_no_block(tmp_path):
    if not hasattr(os,'mkfifo'): pytest.skip('POSIX FIFO')
    fifo=tmp_path/'input';os.mkfifo(fifo)
    assert len((canonical(example())+'\n').encode()) == 432
    # No writer: this would block forever if the old open() were reached.
    with pytest.raises(LabError,match='regular'): read_examples(fifo,max_bytes=16)


def test_r3_socket_and_directory(tmp_path):
    with pytest.raises(LabError,match='regular'): read_examples(tmp_path)
    if not hasattr(socket,'AF_UNIX'): pytest.skip('Unix socket')
    with socket.socket(socket.AF_UNIX) as sock:
        path=tmp_path/'socket';sock.bind(str(path))
        with pytest.raises(LabError,match='regular'): read_examples(path)


def test_r3_opened_descriptor_is_checked(tmp_path, monkeypatch):
    import lia_lab.datasets as ds
    path=tmp_path/'input';path.write_text(canonical(example())+'\n')
    original=os.fstat
    from types import SimpleNamespace
    monkeypatch.setattr(ds.os,'fstat',lambda fd:SimpleNamespace(st_mode=0o020000, st_size=0))
    with pytest.raises(LabError,match='opened'):read_examples(path)
    monkeypatch.setattr(ds.os,'fstat',original)


def test_r3_growth_after_fstat_and_line_bound(tmp_path, monkeypatch):
    import lia_lab.datasets as ds
    path=tmp_path/'input';payload=(canonical(example())+'\n').encode();path.write_bytes(payload)
    original=os.fstat
    def grow(fd):
        old=original(fd)
        with path.open('ab') as stream:stream.write(b'x'*4096)
        return old
    monkeypatch.setattr(ds.os,'fstat',grow)
    with pytest.raises(LabError,match='limit'):read_examples(path,max_bytes=len(payload))
    monkeypatch.setattr(ds.os,'fstat',original)
    path.write_bytes(b'x'*10000)
    with pytest.raises(LabError,match='line limit'):read_examples(path,max_line_bytes=16)
    path.write_bytes(payload)
    assert len(read_examples(path,max_bytes=len(payload),max_line_bytes=len(payload))) == 1


@pytest.mark.parametrize('schema',[{'$ref':'#'}, {'$defs':{'a':{'$ref':'#/$defs/b'},'b':{'$ref':'#/$defs/a'}},'$ref':'#/$defs/a'}])
def test_r4_nonprogress_cycles_controlled(schema):
    with pytest.raises(LabError,match='circular|recursive'):validate_tool_arguments(schema,{})


def test_r4_progressing_recursive_data_and_external_block():
    schema={'$defs':{'node':{'type':'object','properties':{'child':{'$ref':'#/$defs/node'}}}},'$ref':'#/$defs/node'}
    validate_tool_arguments(schema,{'child':{'child':{}}})
    for ref in ['https://untrusted.invalid/schema','file:///etc/passwd']:
        with pytest.raises(LabError,match='external'):validate_tool_schema({'$ref':ref})
    validate_tool_arguments({'type':'object'},{'$ref':'a literal argument, not a schema'})


def test_r4_complexity_depth_and_suite(tmp_path, capsys, snapshot):
    schema={};cursor=schema
    for _ in range(60): cursor['not']={};cursor=cursor['not']
    with pytest.raises(LabError,match='depth'):validate_tool_schema(schema)
    with pytest.raises(LabError,match='complexity'):validate_tool_schema({'enum':list(range(5000))})
    suite=load('configs/inference-suite.json');suite['cases'][-1]['tools'][0]['function']['parameters']={'$ref':'#'}
    with pytest.raises(LabError):validate_suite(suite)
    from lia_lab.io import atomic_json
    from lia_lab.cli import main
    path=tmp_path/'suite.json';atomic_json(path,suite)
    rc=main(['plan-inference','--snapshot',str(snapshot[0]),'--snapshot-manifest',str(snapshot[1]),
        '--suite',str(path),'--research-root',str(tmp_path/'research'),'--approved-root',str(tmp_path/'approved'),
        '--containment','portable-process','--run-id','cycle-test','--output',str(tmp_path/'plan.json')])
    assert rc == 2
    assert 'Traceback' not in capsys.readouterr().err
    assert not (tmp_path/'plan.json').exists()


@pytest.mark.parametrize('tree',['docs','src'])
def test_r5_symlink_tree_roots(tmp_path,tree, require_symlink):
    actual=tmp_path/'actual';actual.mkdir();(actual/'a.md').write_text('fixture')
    (tmp_path/tree).symlink_to(actual,target_is_directory=True)
    with pytest.raises(LabError,match='symlink'):module('verify_repository').package_paths(tmp_path)


def test_r5_intermediate_and_descendant(tmp_path,monkeypatch, require_symlink):
    v=module('verify_repository');actual=tmp_path/'actual';(actual/'docs').mkdir(parents=True)
    (tmp_path/'nested').symlink_to(actual,target_is_directory=True)
    monkeypatch.setattr(v,'TREES',('nested/docs',))
    with pytest.raises(LabError,match='symlink'):v.package_paths(tmp_path)
    (tmp_path/'nested').unlink();(tmp_path/'nested/docs').mkdir(parents=True)
    (tmp_path/'nested/docs/a.md').write_text('fixture')
    assert len(v.package_paths(tmp_path)) == 1
    (tmp_path/'nested/docs/link').symlink_to(tmp_path/'missing')
    with pytest.raises(LabError,match='symlink'):v.package_paths(tmp_path)


def test_r1_namespaced_root_disguised_as_slash_unknown(tmp_path):
    proc, mount = cgroup(tmp_path)
    (mount/'memory.max').write_text('max')
    assert memory(proc)['available_bytes'] is None


def test_r4_dialect_cannot_drop_budget_and_literals_not_rewritten():
    uri='https://json-schema.org/draft/2020-12/schema'
    with pytest.raises(LabError,match='circular|recursive'):
        validate_tool_arguments({'$schema':uri,'$ref':'#'}, {})
    literal={'$schema':uri}
    validate_tool_arguments({'const':literal}, literal)
    with pytest.raises(LabError):validate_tool_arguments({'const':literal}, {})


def test_r4_evaluation_budget_for_exponential_valid_ref_graph():
    schema={'$defs':{'n0':{}},'$ref':'#/$defs/n14'}
    for i in range(1,15):
        schema['$defs']['n'+str(i)]={'allOf':[{'$ref':'#/$defs/n'+str(i-1)} for _ in range(2)]}
    with pytest.raises(LabError,match='complexity'):validate_tool_arguments(schema,{})


def test_r1_unknown_envelope_blocks_preflight(snapshot,tmp_path,monkeypatch):
    from lia_lab import inference
    from test_inference import run_fixture
    report=inference.doctor();report['ram']=memory(tmp_path/'absent-proc')
    report['dependencies'].update(torch='stub',transformers='stub')
    monkeypatch.setattr(inference,'doctor',lambda _:synthetic_ram(report))
    monkeypatch.setattr(inference,'supervise',lambda *a:pytest.fail('unknown RAM launched worker'))
    result=run_fixture(snapshot,tmp_path)
    assert result['status']=='blocked' and any('RAM unknown' in b for b in result['blockers'])


def test_r1_mountinfo_escaped_space(tmp_path):
    proc,mount=cgroup(tmp_path)
    moved=mount.with_name('mount space');mount.rename(moved)
    (proc/'self/mountinfo').write_text('42 1 0:1 / '+str(moved).replace(' ',r'\040')+' rw - cgroup2 cgroup rw\n')
    assert memory(proc)['available_bytes'] == 4*1024**2
