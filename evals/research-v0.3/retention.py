"""Lossless candidate retention with bounded Git-sized archive parts.

Scientific artifacts and source are retained verbatim. Reconstructable software
wheels are identified by exact filename/hash and restored before verification.
This is transport/bookkeeping, not a scientific scorer or candidate edit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

PART_BYTES=32*1024*1024


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def paths(root):
    for directory,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[name for name in dirs if name not in ('.git','.tmp','__pycache__','.cache')
                 and not name.startswith('.venv') and not (Path(directory)/name/'pyvenv.cfg').exists()]
        if any((Path(directory)/name).is_symlink() for name in dirs):
            raise ValueError('Unexpected retained directory symlink: '+directory)
        for name in files:
            if name in ('.DS_Store','.mutex') or name.endswith(('.pyc','.pyo')):continue
            path=Path(directory)/name
            if path.is_symlink():raise ValueError('Unexpected retained symlink: '+str(path))
            if path.is_file():yield path


def collect(source,destination):
    source,destination=Path(source).resolve(),Path(destination).resolve()
    if destination.exists():raise ValueError('Retention destination exists; do not overwrite a run package')
    destination.mkdir(parents=True)
    entries={str(p.relative_to(source)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths(source))}
    wheels={name:entry for name,entry in entries.items() if name.endswith('.whl') and
            (name.startswith('inputs/materials/wheels/') or name.startswith('inputs/wheels/'))}
    included={name:entry for name,entry in entries.items() if name not in wheels}
    with tempfile.TemporaryDirectory(prefix='allagma-retention-') as temporary:
        archive=Path(temporary)/'candidate.tar.gz'
        with tarfile.open(archive,'w:gz') as handle:
            for name in included:
                handle.add(source/name,arcname=name,recursive=False)
        parts=[]
        with archive.open('rb') as handle:
            index=1
            while data:=handle.read(PART_BYTES):
                path=destination/f'candidate.tar.gz.part-{index:03d}';path.write_bytes(data)
                parts.append({'path':path.name,'bytes':len(data),'sha256':sha(path)});index+=1
        archive_sha=sha(archive)
    for name,entry in entries.items():
        if sha(source/name)!=entry['sha256']:raise ValueError('Candidate changed during collection: '+name)
    manifest_errors=[]
    supplied=source/'artifact-manifest.json'
    if supplied.exists():
        try:
            value=json.loads(supplied.read_text());declared=value.get('files',value)
            if isinstance(declared,dict):declared=[{'path':k,**({'sha256':v} if isinstance(v,str) else v)} for k,v in declared.items()]
            for entry in declared:
                name=entry['path'];path=(source/name).resolve()
                if source not in path.parents or not path.is_file() or sha(path)!=entry['sha256']:
                    manifest_errors.append(name)
        except (ValueError,KeyError,TypeError,AttributeError):manifest_errors.append('unsupported-or-invalid-manifest-format')
    else:manifest_errors.append('manifest-missing')
    result={'format':'allagma-retained-package-v1','source':str(source),'archive_sha256':archive_sha,'parts':parts,
            'files':included,'external_wheels':wheels,'artifact_manifest_errors':manifest_errors,
            'scope':'Verbatim artifacts/source; software wheels require exact-hash hydration. No claim of scientific completion.',
            'excluded':'Virtual environments, caches and mutation locks. Terminal compute queues are retained as evidence.'}
    (destination/'package-index.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return {'retained_files':len(included),'wheel_files':len(wheels),'archive_parts':len(parts),'manifest_errors':manifest_errors}


def confined(root,name):
    relative=Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Invalid retained path: '+name)
    path=(root/relative).resolve()
    if root not in path.parents:raise ValueError('Retained path escapes package: '+name)
    return path


def supplement(source,package):
    """Add omitted terminal-queue bytes without replacing historical archives."""
    source,package=Path(source).resolve(),Path(package).resolve()
    index=json.loads((package/'package-index.json').read_text())
    output=package/'terminal-queue'
    receipt=package/'terminal-queue-index.json'
    if output.exists() or receipt.exists():raise ValueError('Terminal queue supplement already exists')
    for name,entry in {**index['files'],**index['external_wheels']}.items():
        if sha(confined(source,name))!=entry['sha256']:
            raise ValueError('Original candidate changed before queue retention: '+name)
    entries={}
    queue=source/'.compute'
    if queue.is_symlink():raise ValueError('Unexpected queue symlink')
    for path in sorted(paths(queue)):
        name=str(path.relative_to(source))
        if name in index['files']:continue
        target=confined(output.resolve(),name)
        entry={'sha256':sha(path),'bytes':path.stat().st_size}
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
        if sha(target)!=entry['sha256'] or sha(path)!=entry['sha256']:
            raise ValueError('Queue changed during retention: '+name)
        entries[name]=entry
    result={'format':'allagma-terminal-queue-supplement-v1','files':entries,
            'package_index_sha256':sha(package/'package-index.json'),
            'scope':'Verbatim terminal request/response/log bytes omitted by the original transport. No candidate edit, new execution or scientific repair.'}
    receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return {'supplemental_files':len(entries),'scope':result['scope']}


def restore(package,destination,*,wheel_cache=None,download_wheels=False):
    package,destination=Path(package).resolve(),Path(destination).resolve()
    if destination.exists():raise ValueError('Restore to a new directory')
    index=json.loads((package/'package-index.json').read_text())
    destination.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='allagma-restore-') as temporary:
        archive=Path(temporary)/'candidate.tar.gz'
        with archive.open('wb') as out:
            for part in index['parts']:
                path=package/part['path']
                if sha(path)!=part['sha256']:raise ValueError('Archive part changed')
                with path.open('rb') as handle:shutil.copyfileobj(handle,out)
        if sha(archive)!=index['archive_sha256']:raise ValueError('Reassembled archive changed')
        with tarfile.open(archive) as handle:
            for member in handle.getmembers():
                if member.name not in index['files'] or not member.isfile() or Path(member.name).is_absolute() or '..' in Path(member.name).parts:
                    raise ValueError('Unexpected archive member')
            handle.extractall(destination,filter='data')
        for name,entry in index['external_wheels'].items():
            path=destination/name;path.parent.mkdir(parents=True,exist_ok=True)
            filename=path.name;found=[]
            if wheel_cache:found=list(Path(wheel_cache).rglob(filename))
            matching=next((p for p in found if sha(p)==entry['sha256']),None)
            if matching:shutil.copyfile(matching,path)
            elif download_wheels:
                if not re.fullmatch(r'[A-Za-z0-9_.]+-[A-Za-z0-9_.+!]+-[A-Za-z0-9_.-]+\.whl',filename):
                    raise ValueError('Invalid dependency wheel filename')
                project,version=filename.split('-',2)[:2]
                subprocess.run([sys.executable,'-m','pip','download','--no-deps','--only-binary=:all:',
                                '--dest',str(path.parent),project+'=='+version],check=True)
            else:raise ValueError('Exact wheel unavailable; supply a cache or explicitly enable download: '+filename)
            if not path.exists() or sha(path)!=entry['sha256']:raise ValueError('Downloaded wheel identity differs: '+filename)
    supplemental={}
    receipt=package/'terminal-queue-index.json'
    if receipt.exists():
        addition=json.loads(receipt.read_text())
        if addition['package_index_sha256']!=sha(package/'package-index.json'):
            raise ValueError('Terminal queue supplement targets a different archive index')
        supplemental=addition['files']
        for name,entry in supplemental.items():
            if not name.startswith('.compute/') or name in index['files'] or name in index['external_wheels']:
                raise ValueError('Unexpected supplemental path')
            source=confined((package/'terminal-queue').resolve(),name)
            target=confined(destination,name)
            if not source.is_file() or sha(source)!=entry['sha256']:
                raise ValueError('Terminal queue supplement changed: '+name)
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    for name,entry in {**index['files'],**index['external_wheels'],**supplemental}.items():
        path=destination/name
        if not path.is_file() or sha(path)!=entry['sha256']:raise ValueError('Restored file differs: '+name)
    return {'status':'pass','restored_files':len(index['files'])+len(index['external_wheels'])+len(supplemental),
            'terminal_queue_supplement_files':len(supplemental),
            'scope':'Exact file restoration and dependency hydration; execution/recomputation are separate checks'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['collect','supplement','restore'])
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--wheel-cache',type=Path);parser.add_argument('--download-wheels',action='store_true')
    args=parser.parse_args()
    if args.operation=='collect':result=collect(args.source,args.destination)
    elif args.operation=='supplement':result=supplement(args.source,args.destination)
    else:result=restore(args.source,args.destination,wheel_cache=args.wheel_cache,download_wheels=args.download_wheels)
    print(json.dumps(result,indent=2))
