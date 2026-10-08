"""Preserve audit v1 and create a narrowly corrected terminal verifier and seal."""
from pathlib import Path
import hashlib,json,shutil
from package import make_manifest

old=Path('study/verify_package.py').read_text()
needle="                assert not p.is_absolute() and '..' not in p.parts\n"
replacement="""                if p.is_absolute():
                    assert 'module_id' in obj and 'bundle_id' in obj, 'Unexpected absolute artifact reference'
                    p=p.relative_to(Path.cwd())
                assert '..' not in p.parts
"""
assert old.count(needle)==1
new=old.replace(needle,replacement)
new=new.replace("result={'status':'passed',", "result={'status':'passed','verifier_source_sha256':sha('study/verify_package_v2.py'),")
target=Path('study/verify_package_v2.py');assert not target.exists();target.write_text(new)
previous=Path('artifact-manifest-v1.json');assert not previous.exists();shutil.copyfile('artifact-manifest.json',previous)
record={'reason':'The first terminal audit incorrectly applied the relative-artifact-path rule to absolute canonical module paths returned by the locked Allagma resolver. The new verifier accepts an absolute path only for a module entry containing module_id and bundle_id, requires it to be within the workspace, and still validates its hash. All ordinary artifact references remain relative.','failed_request_id':'d50380787e554cebb84f8a71cafc26b4','old_verifier':{'path':'study/verify_package.py','sha256':hashlib.sha256(old.encode()).hexdigest()},'new_verifier':{'path':str(target),'sha256':hashlib.sha256(new.encode()).hexdigest()},'scientific_changes':False,'report_unchanged_sha256':hashlib.sha256(Path('REPORT.md').read_bytes()).hexdigest(),'manifest_revision':2}
Path('evidence/audit-correction.json').write_text(json.dumps(record,indent=2)+'\n')
make_manifest()
manifest=json.loads(Path('artifact-manifest.json').read_text())
manifest['revision']=2
manifest['previous_manifest']={'path':str(previous),'sha256':hashlib.sha256(previous.read_bytes()).hexdigest()}
manifest['files'].append({'path':str(previous),'sha256':hashlib.sha256(previous.read_bytes()).hexdigest(),'bytes':previous.stat().st_size})
manifest['files'].sort(key=lambda x:x['path'])
Path('artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(record,indent=2))
