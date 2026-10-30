"""All snapshots here are tiny synthetic zero tensors, NOT language-model weights."""
import pytest
import numpy as np
from safetensors.numpy import save_file
from lia_lab.checkpoints import seal_snapshot
from lia_lab.io import atomic_json

@pytest.fixture
def snapshot(tmp_path):
    directory = tmp_path / 'snapshot'
    directory.mkdir()
    atomic_json(directory / 'config.json', {'model_type': 'qwen3', 'architectures':['Qwen3ForCausalLM']})
    atomic_json(directory / 'tokenizer_config.json', {'chat_template': 'synthetic-test-only'})
    (directory / 'LICENSE').write_text('SYNTHETIC placeholder: not actual Apache license review')
    save_file({'fixture': np.zeros((2, 3), dtype=np.float32)}, directory / 'model.safetensors')
    manifest = tmp_path / 'snapshot-manifest.json'
    seal_snapshot(directory, manifest, 'fictional/fixture-only', 'a'*40, 'Apache-2.0', 'LICENSE', 'TEST-ATTESTATION-NOT-REAL-AUTHORIZATION')
    return directory, manifest

