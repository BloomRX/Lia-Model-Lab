"""R6 integration of the exact CI checker with committed synthetic Git history."""
import json
import subprocess
from test_review_resources import module
import pytest


def test_r6_committed_whitespace_fails_pr_and_push_clean_checkout(tmp_path):
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=tmp_path,text=True).strip()
    git('init','-q')
    git('config','user.name','Synthetic fixture');git('config','user.email','fixture@invalid.example')
    path=tmp_path/'file.txt';path.write_text('clean\n');git('add','.');git('commit','-qm','clean')
    base=git('rev-parse','HEAD')
    path.write_text('bad trailing whitespace \n');git('add','.');git('commit','-qm','bad whitespace fixture')
    head=git('rev-parse','HEAD');assert not git('status','--porcelain')
    checker=module('check_whitespace')
    pr={'pull_request':{'base':{'sha':base},'head':{'sha':head}}}
    push={'before':base,'after':head}
    assert checker.check('pull_request',pr,tmp_path) != 0
    assert checker.check('push',push,tmp_path) != 0
    assert checker.check('push',{'before':'0'*40,'after':head},tmp_path) != 0
    path.write_text('clean fixed\n');git('add','.');git('commit','-qm','fix whitespace')
    fixed=git('rev-parse','HEAD')
    assert checker.check('pull_request',{'pull_request':{'base':{'sha':base},'head':{'sha':fixed}}},tmp_path) == 0
    assert checker.check('push',{'before':head,'after':fixed},tmp_path) == 0
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        checker.revisions('push',{'before':'a'*40,'after':fixed},tmp_path)
    with pytest.raises(ValueError):checker.revisions('unknown',push,tmp_path)


def test_r6_workflow_uses_committed_checker_and_full_history():
    from lia_lab.io import load
    workflow=load('.github/workflows/verify.yml')
    steps=workflow['jobs']['verify']['steps']
    assert any(step.get('run')=='python scripts/check_whitespace.py' for step in steps)
    assert any(step.get('uses')=='actions/checkout@v5' and step.get('with',{}).get('fetch-depth')==0 for step in steps)


def test_first_feature_push_checks_own_changes_preserves_inherited_history(tmp_path):
    def git(*args): return subprocess.check_output(['git',*args],cwd=tmp_path,text=True).strip()
    git('init','-q');git('config','user.name','Synthetic fixture');git('config','user.email','fixture@invalid.example')
    (tmp_path/'brand.md').write_text('historical Markdown hard break  \n')
    git('add','.');git('commit','-qm','historical fixture')
    base=git('rev-parse','HEAD');git('update-ref','refs/remotes/origin/main',base)
    file=tmp_path/'change.txt';file.write_text('clean feature\n');git('add','.');git('commit','-qm','feature')
    head=git('rev-parse','HEAD')
    event=dict(before='0'*40,after=head,ref='refs/heads/codex/fixture',repository={'default_branch':'main'})
    checker=module('check_whitespace')
    assert checker.revisions('push',event,tmp_path)==(base,head)
    assert checker.check('push',event,tmp_path)==0
    file.write_text('new bad whitespace \n');git('add','.');git('commit','-qm','bad new change')
    event['after']=git('rev-parse','HEAD')
    assert checker.check('push',event,tmp_path)!=0
    event['ref']='refs/heads/main'
    assert checker.check('push',event,tmp_path)!=0  # first default push still checks all files
