"""All snapshots here are tiny synthetic zero tensors, NOT language-model weights."""
import pytest
from pathlib import Path
import numpy as np
from safetensors.numpy import save_file
from lia_lab.checkpoints import seal_snapshot
from lia_lab.io import atomic_json
from support_checkpoint import CONFIG, SHAPES


@pytest.fixture
def require_symlink(tmp_path):
    link = tmp_path / 'capability-link'
    try:
        link.symlink_to(tmp_path / 'missing')
    except OSError as exc:
        if getattr(exc, 'winerror', None) == 1314:
            pytest.skip('Windows account lacks symlink privilege (WinError 1314)')
        raise
    link.unlink()


@pytest.fixture
def snapshot(tmp_path):
    directory = tmp_path / 'snapshot'
    directory.mkdir()
    atomic_json(directory / 'config.json', CONFIG)
    atomic_json(directory / 'tokenizer_config.json', {'chat_template': 'synthetic-test-only'})
    (directory / 'LICENSE').write_text('SYNTHETIC placeholder: not actual Apache license review')
    save_file({name: np.zeros(shape, dtype=np.float32) for name, shape in SHAPES.items()}, directory / 'model.safetensors')
    manifest = tmp_path / 'snapshot-manifest.json'
    seal_snapshot(directory, manifest, 'fictional/fixture-only', 'a'*40, 'Apache-2.0', 'LICENSE', 'TEST-ATTESTATION-NOT-REAL-AUTHORIZATION')
    return directory, manifest
