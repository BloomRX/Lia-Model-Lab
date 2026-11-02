"""OS resource tests use disposable Python children only, not Torch or models."""
import json
import os
import subprocess
import sys
import pytest
from lia_lab.containment import policy, supervise
from lia_lab.io import LabError


def test_portable_is_explicitly_not_sandbox():
    p=policy('portable-process',10,'cpu')
    assert p['security_sandbox'] is False and p['network_policy']=='not-applied'
    assert p['os_resource_limits'].startswith('not-applied')


def test_no_silent_platform_or_gpu_fallback(monkeypatch):
    with pytest.raises(LabError):policy('linux-rlimit',10,'cuda')
    monkeypatch.setattr(sys,'platform','win32')
    with pytest.raises(LabError):policy('linux-rlimit',10,'cpu')


@pytest.mark.skipif(sys.platform!='linux',reason='actual Linux resource API only')
def test_real_linux_rlimits_disposable_child():
    code="from lia_lab.containment import *;import json;print(json.dumps(apply_limits(policy('linux-rlimit',10,'cpu'))))"
    result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,check=True,timeout=10)
    p=json.loads(result.stdout)
    assert p['os_resource_limits']=='applied'
    assert p['effective_limits']['open_files']<=128 and p['effective_limits']['file_bytes']<=64*1024**2
    assert p['network_policy']=='not-applied'


def test_real_worker_timeout(tmp_path):
    with (tmp_path/'log').open('wb') as log:
        with pytest.raises(subprocess.TimeoutExpired):
            supervise([sys.executable,'-c','import time;time.sleep(30)'],dict(os.environ),log,0.1)


@pytest.mark.skipif(sys.platform!='linux',reason='actual Linux namespace API only')
def test_real_linux_network_namespace_or_explicit_refusal(tmp_path):
    from lia_lab.containment import launch_command
    settings=policy('linux-netns-rlimit',10,'cpu')
    code="from lia_lab.containment import apply_limits;import json,sys;print(json.dumps(apply_limits(json.loads(sys.argv[1]))))"
    result=subprocess.run(launch_command([sys.executable,'-c',code,json.dumps(settings)],settings),
                          capture_output=True,text=True,timeout=10)
    if result.returncode:
        # A locked-down CI runner may forbid user namespaces; it must FAIL rather than fallback.
        assert 'Operation not permitted' in result.stderr or 'unshare' in result.stderr
    else:
        applied=json.loads(result.stdout)
        assert applied['network_policy']=='applied-new-linux-IP-network-namespace'
        assert applied['effective_netns_inode']!=settings['supervisor_netns_inode']
        assert not applied['security_sandbox']


def test_required_netns_rejects_plain_process():
    if sys.platform!='linux':pytest.skip('Linux namespace validation only')
    from lia_lab.containment import apply_limits
    with pytest.raises(LabError,match='not applied'):apply_limits(policy('linux-netns-rlimit',10,'cpu'))
