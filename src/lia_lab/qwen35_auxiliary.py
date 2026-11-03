"""Explicit preservation of the pinned checkpoint's 15 MTP tensors.

Transformers 5.22.1's official AR forward does not implement MTP decoding and
filters mtp.* while loading. Retain the verified auxiliary weights as frozen
Parameters, without changing the official model class/forward or enabling MTP.
This function is called only by the authorized worker's weight-loading path.
"""
from .io import LabError


def restore(model, snapshot, expected, dtype):
    import torch
    from pathlib import Path
    from safetensors import safe_open
    from .checkpoints import tensor_inventory
    auxiliary = {k:v for k,v in expected.items() if k.startswith('mtp.')}
    if len(auxiliary) != 15 or hasattr(model, 'mtp'):
        raise LabError('unreviewed MTP runtime layout; no generic auxiliary fallback')
    inventory = tensor_inventory(snapshot)
    module = torch.nn.Module()
    # The exact names/shapes/dtypes were checked by checkpoint_capacity before
    # from_pretrained. No regex-based exception for unknown mtp names is allowed.
    for shard in sorted({inventory[k]['shard'] for k in auxiliary}):
        with safe_open(Path(snapshot)/shard, framework='pt', device='cpu') as handle:
            for name, shape in auxiliary.items():
                if inventory[name]['shard'] != shard:
                    continue
                tensor = handle.get_tensor(name)
                if tuple(tensor.shape) != shape:
                    raise LabError('MTP tensor changed while loading')
                node = module
                parts = name.split('.')[1:]
                for component in parts[:-1]:
                    if component not in node._modules:
                        node.add_module(component, torch.nn.Module())
                    node = node._modules[component]
                node.register_parameter(parts[-1], torch.nn.Parameter(tensor.to(dtype=dtype), requires_grad=False))
    model.add_module('mtp', module)
    return len(auxiliary)
