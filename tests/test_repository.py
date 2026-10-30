"""Tests for the verifier itself, not merely its current happy-path report."""
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('verify_repository',Path(__file__).parents[1]/'scripts/verify_repository.py')
verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)


def test_repository_parsers_and_references():
    report=verify.validate(check_manifest=False)
    assert report['skills']==9 and report['agents']==7
    assert report['json']>0 and report['yaml']>0 and report['toml']>0


def test_manifest_full_coverage_and_hash_change(tmp_path):
    (tmp_path/'README.md').write_text('initial')
    (tmp_path/'docs').mkdir();(tmp_path/'docs/a.md').write_text('doc')
    first=verify.manifest(tmp_path)
    assert len(first['files'])==2
    (tmp_path/'README.md').write_text('changed')
    assert verify.manifest(tmp_path)!=first
    (tmp_path/'docs/a.md').unlink()
    assert len(verify.manifest(tmp_path)['files'])==1


def test_manifest_rejects_symlinks(tmp_path):
    (tmp_path/'README.md').symlink_to('/etc/hostname')
    with pytest.raises(ValueError):verify.manifest(tmp_path)


def test_broken_link_detection(tmp_path):
    (tmp_path/'README.md').write_text('[bad](missing.md)')
    with pytest.raises(ValueError,match='broken link'):verify.validate(tmp_path,check_manifest=False)
