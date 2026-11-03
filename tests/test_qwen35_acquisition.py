"""Bounded fictional HTTP replies only; never download models in test/CI."""
import io
import hashlib
import importlib.util
from pathlib import Path
import pytest
from lia_lab.io import LabError

spec=importlib.util.spec_from_file_location('acquire_qwen35',Path('scripts/acquire_qwen35.py'))
acquire=importlib.util.module_from_spec(spec);spec.loader.exec_module(acquire)


def item(data):
    return dict(name='fixture.txt',bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
        git_blob_sha1=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest(),url='https://example.invalid/fixture')


class Reply(io.BytesIO):
    def __init__(self,data,status=200,content_range=None):
        super().__init__(data);self.status=status;self.headers={'Content-Range':content_range} if content_range else {}


def test_explicit_fetch_and_no_overwrite_verified_file(tmp_path):
    data=b'fixture';target=tmp_path/'file';partial=tmp_path/'partial'
    acquire.fetch(item(data),target,partial,lambda *a,**k:Reply(data))
    assert target.read_bytes()==data and not partial.exists()
    acquire.fetch(item(data),target,partial,lambda *a,**k:pytest.fail('verified file should not download'))
    target.write_bytes(b'changed')
    with pytest.raises(LabError,match='refusing overwrite'):acquire.fetch(item(data),target,partial)
    assert target.read_bytes()==b'changed'


@pytest.mark.parametrize('range_honored',[True,False])
def test_resume_or_restart_unverified_partial(tmp_path,range_honored):
    data=b'fixture';partial=tmp_path/'partial';partial.write_bytes(data[:2]);target=tmp_path/'file'
    def respond(request,**kwargs):
        assert request.headers['Range']=='bytes=2-'
        return Reply(data[2:],206,'bytes 2-6/7') if range_honored else Reply(data)
    acquire.fetch(item(data),target,partial,respond)
    assert target.read_bytes()==data


@pytest.mark.parametrize('problem',['hash','oversize','range'])
def test_corruption_or_bad_resume_never_published(tmp_path,problem):
    data=b'fixture';partial=tmp_path/'partial';target=tmp_path/'file';expected=item(data)
    if problem=='hash':expected['sha256']='0'*64
    if problem=='range':partial.write_bytes(b'fi')
    def respond(*args,**kwargs):
        if problem=='range':return Reply(data[2:],206,'bytes 3-6/7')
        return Reply(data+b'extra' if problem=='oversize' else data)
    with pytest.raises(LabError):acquire.fetch(expected,target,partial,respond)
    assert not target.exists()


def test_models_never_inside_research_or_approved_or_checkout(tmp_path):
    for storage in (tmp_path/'r/models',tmp_path/'a/models',acquire.ROOT/'models'):
        with pytest.raises(LabError,match='disjoint'):acquire.storage_path(storage,tmp_path/'r',tmp_path/'a')
    assert acquire.storage_path(tmp_path/'models',tmp_path/'r',tmp_path/'a')==tmp_path/'models'


def test_partial_symlink_is_not_overwritten(tmp_path,require_symlink):
    data=b'fixture';outside=tmp_path/'outside';outside.write_bytes(data)
    partial=tmp_path/'partial';partial.symlink_to(outside)
    with pytest.raises(LabError,match='symlink'):acquire.fetch(item(data),tmp_path/'target',partial)
    assert outside.read_bytes()==data
