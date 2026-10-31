"""Weight-free diagnostics. Device nodes are evidence, not driver compatibility."""
import importlib.metadata
import os
import platform
import shutil
from pathlib import Path


def dependencies():
    result = {}
    for name in ('torch', 'transformers', 'peft', 'bitsandbytes', 'safetensors', 'numpy', 'tokenizers', 'huggingface-hub', 'accelerate'):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def memory():
    """Linux available RAM bounded by cgroup v2; null on unimplemented platforms."""
    try:
        values = {line.split(':')[0]: int(line.split()[1]) * 1024
                  for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line}
        available, total = values['MemAvailable'], values['MemTotal']
        limit_path = Path('/sys/fs/cgroup/memory.max')
        if not limit_path.exists():
            # cgroup v1/unknown controller layout must not be reported as host RAM
            # available to the worker. A separate sizing implementation is needed.
            return {'total_bytes': None, 'available_bytes': None}
        if limit_path.read_text().strip() != 'max':
            limit = int(limit_path.read_text())
            total = min(total, limit)
            available = min(available, max(0, limit - int(Path('/sys/fs/cgroup/memory.current').read_text())))
        return {'total_bytes': total, 'available_bytes': available}
    except (OSError, ValueError, KeyError):
        return {'total_bytes': None, 'available_bytes': None}


def rss():
    try:
        return next(int(line.split()[1]) * 1024 for line in
                    Path('/proc/self/status').read_text().splitlines() if line.startswith('VmRSS:'))
    except (OSError, StopIteration, ValueError):
        return None


def doctor(storage='.'):
    disk = shutil.disk_usage(storage)
    return {'schema_version': 1, 'evidence': 'observed-environment-not-inference',
            'python': platform.python_version(), 'os': platform.system(), 'machine': platform.machine(),
            'cpu_count': os.cpu_count(), 'ram': memory(), 'disk_free_bytes': disk.free,
            'device_nodes': {p: Path(p).exists() for p in ('/dev/nvidia0', '/dev/kfd', '/dev/dri')},
            'dependencies': dependencies(), 'gpu_runtime_verified': False,
            'recommendations': ['No automatic CUDA selection: choose cpu/cuda/rocm/mps explicitly.',
                'With limited RAM prefer a small reviewed GGUF on CPU/Vulkan in llama.cpp; that backend is not yet implemented by this CLI.',
                'For Transformers CPU reference use float32; memory is checked again against the real tensor inventory.',
                'Qwen3.5-4B is not a safe unquantized target on a 4 GB host; use a larger authorized environment.'],
            'note': 'Nodes/packages do not prove CUDA/ROCm/Vulkan support; worker probes torch after authorization.'}
