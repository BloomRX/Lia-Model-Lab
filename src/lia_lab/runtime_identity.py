"""Metadata/source fingerprints without importing ML or accessing the network."""
import hashlib
import importlib.metadata
import platform
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse
from .io import LabError


def locked_versions():
    lock=Path(__file__).resolve().parents[2]/'requirements-ml-windows-cpu.lock'
    expected={}
    if not lock.exists():return expected
    for line in lock.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):continue
        if ' @ ' in line:
            name,url=line.split(' @ ',1)
            if name not in {'torch','torchvision'} or '#sha256=' not in url:
                raise LabError('unreviewed ML lock URL')
            version=unquote(urlparse(url).path).split('/')[-1].split('-')[1]
        elif '==' in line:name,version=line.split('==',1)
        else:raise LabError('ML lock must pin every dependency')
        expected[name]=version
    return expected


def locked_mismatches(identity):
    if not identity.get('ml_lock_sha256'):return ['pinned ML runtime lock missing']
    return [f'ML runtime mismatch: {name} expected {version}, observed {identity["locked_package_versions"].get(name)}'
            for name,version in locked_versions().items() if identity['locked_package_versions'].get(name)!=version]


def fingerprint():
    packages = {}
    for name in ('torch','torchvision','transformers','tokenizers','safetensors','numpy','pillow','huggingface-hub','accelerate'):
        try:
            dist=importlib.metadata.distribution(name)
            paths = {'transformers': ['transformers/models/qwen3_5/modeling_qwen3_5.py',
                'transformers/models/qwen3_5/configuration_qwen3_5.py', 'transformers/models/auto/modeling_auto.py',
                'transformers/processing_utils.py','transformers/models/qwen3_vl/processing_qwen3_vl.py'],
                'torch':['torch/__init__.py','torch/version.py']}.get(name,[])
            packages[name]=dict(version=dist.version, source_sha256={p:hashlib.sha256(Path(dist.locate_file(p)).read_bytes()).hexdigest() for p in paths})
        except importlib.metadata.PackageNotFoundError:
            packages[name]=None
    lock=Path(__file__).resolve().parents[2]/'requirements-ml-windows-cpu.lock'
    actual={}
    for name in locked_versions():
        try:actual[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:actual[name]=None
    return dict(python=platform.python_version(),executable=str(Path(sys.executable).resolve()),
        platform=sys.platform,packages=packages,locked_package_versions=actual,
        ml_lock_sha256=hashlib.sha256(lock.read_bytes()).hexdigest() if lock.exists() else None)
