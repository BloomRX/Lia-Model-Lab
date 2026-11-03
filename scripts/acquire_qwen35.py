#!/usr/bin/env python3
"""Explicit, unauthenticated acquisition of one pinned public checkpoint.

No model loading, grants, license approval or network on import. Default is
inventory/disk planning; --download explicitly acquires and verifies bytes.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lia_lab.io import LabError, load, atomic_json, roots


def hashes(path):
    sha=hashlib.sha256();blob=hashlib.sha1(f'blob {path.stat().st_size}\0'.encode())
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(4*1024**2),b''):
            sha.update(chunk);blob.update(chunk)
    return dict(sha256=sha.hexdigest(),git_blob_sha1=blob.hexdigest())


def verified(path,item):
    return (path.is_file() and not path.is_symlink() and path.stat().st_size==item['bytes'] and
            hashes(path)=={k:item[k] for k in ('sha256','git_blob_sha1')})


def fetch(item,target,partial,opener=urllib.request.urlopen):
    if target.exists() or target.is_symlink():
        if not verified(target,item):raise LabError('existing snapshot file failed verification; refusing overwrite')
        return
    if partial.is_symlink():raise LabError('download staging symlink forbidden')
    offset=partial.stat().st_size if partial.exists() else 0
    if offset>item['bytes']:raise LabError('partial download exceeds inventory; investigate before retry')
    if offset<item['bytes']:
        req=urllib.request.Request(item['url'],headers={'Range':f'bytes={offset}-'} if offset else {})
        with opener(req,timeout=60) as response:
            if response.status==206:
                if not response.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
                    raise LabError('upstream resume offset differs')
            elif response.status==200:
                offset=0  # server ignored Range; only the unverified partial may restart
            else:raise LabError('unexpected upstream download status')
            with partial.open('ab' if offset else 'wb') as stream:
                done=offset
                while True:
                    chunk=response.read(min(4*1024**2,item['bytes']-done+1))
                    if not chunk:break
                    done+=len(chunk)
                    if done>item['bytes']:raise LabError('upstream file exceeds pinned byte budget')
                    stream.write(chunk)
    if not verified(partial,item):raise LabError('download size/hash mismatch; partial retained for investigation')
    # No overwrite publication: another writer cannot replace an already-verified snapshot file.
    import os
    os.link(partial,target)
    partial.unlink()


def storage_path(storage,research,approved):
    research,approved=roots(research,approved)
    original=Path(storage).absolute()
    for path in (original,*original.parents):
        if path.is_symlink():raise LabError('storage symlink forbidden')
    storage=original.resolve()
    for other in (ROOT,research,approved):
        if storage.is_relative_to(other) or other.is_relative_to(storage):
            raise LabError('model storage must be disjoint from checkout/research/approved')
    return storage


def acquire(storage,research,approved,download=False):
    storage=storage_path(storage,research,approved)
    inventory=load(ROOT/'configs/qwen35-acquisition.json')
    model,revision=inventory['model_id'],inventory['revision']
    if model!='Qwen/Qwen3.5-0.8B' or revision!='2fc06364715b967f1860aea9cf38778875588b17':
        raise LabError('only the audited official revision is implemented')
    existing=storage
    while not existing.exists():existing=existing.parent
    free=shutil.disk_usage(existing).free
    result=dict(model_id=model,revision=revision,total_bytes=inventory['total_bytes'],disk_free_bytes=free,
                inference_authorized=False,human_license_review_completed=False)
    if not download:return result
    if free<inventory['total_bytes']*2+5*1024**3:raise LabError('insufficient download/staging disk budget')
    with urllib.request.urlopen(f'https://huggingface.co/api/models/{model}/revision/{revision}?blobs=true',timeout=60) as response:
        remote=json.load(response)
    if remote['sha']!=revision or remote.get('gated') is not False or remote.get('private') is not False or remote.get('cardData',{}).get('license')!='apache-2.0':
        raise LabError('upstream revision/public/license metadata changed; no credentials/terms fallback')
    rows={r['rfilename']:r for r in remote['siblings']}
    if set(rows)!={f['name'] for f in inventory['files']}|{'.gitattributes'}:
        raise LabError('upstream file inventory changed')
    target=storage/model/revision;partial=storage/'partial-downloads'/revision
    for path in (target,partial):
        if any(p.is_symlink() for p in (path,*path.parents)) or not path.resolve().is_relative_to(storage):
            raise LabError('snapshot/staging symlink or escaped path forbidden')
        path.mkdir(parents=True,exist_ok=True)
    # License and small metadata before weights. Exact original LICENSE bytes are pinned.
    for item in sorted(inventory['files'],key=lambda f:(f['name'].endswith('.safetensors'),f['name'])):
        name=item['name'];metadata=rows[name]
        if (metadata['size']!=item['bytes'] or metadata['blobId']!=item['upstream_blob_sha1'] or
            item['url']!=f'https://huggingface.co/{model}/resolve/{revision}/{name}'):
            raise LabError('upstream file identity changed')
        if metadata.get('lfs',{}).get('sha256',item['sha256'])!=item['sha256']:
            raise LabError('upstream LFS hash changed')
        fetch(item,target/name,partial/(name+'.partial'))
        print(f"VERIFIED {name}: {item['bytes']} bytes",flush=True)
    result.update(acquired_at_utc=datetime.now(timezone.utc).isoformat(),files=inventory['files'],source=inventory['source'])
    atomic_json(storage/'acquisitions'/f'qwen35-0.8b-{revision}.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('storage','research-root','approved-root'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--download',action='store_true')
    args=parser.parse_args()
    try:
        print(json.dumps(acquire(args.storage,args.research_root,args.approved_root,args.download),indent=2))
        return 0
    except (OSError,ValueError,KeyError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);return 2


if __name__=='__main__':sys.exit(main())
