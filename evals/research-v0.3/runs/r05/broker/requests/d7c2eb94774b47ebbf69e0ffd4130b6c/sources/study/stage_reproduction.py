"""Setup-only staging, venv creation, offline installation and native compilation."""
import argparse,json,shutil,subprocess,sys,venv
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args()
root=Path.cwd();out=root/args.out
assert not out.exists(),'Use a fresh, nonexisting output directory'
out.mkdir(parents=True)
shutil.copytree(root/'study',out/'study',ignore=shutil.ignore_patterns('__pycache__'))
shutil.copytree(root/'.allagma',out/'.allagma',ignore=shutil.ignore_patterns('__pycache__','mutation.lock'))
for name in ['ALLAGMA.md','RESEARCH.md','SCOPE.md']:
    shutil.copyfile(root/name,out/name)
campaign=out/'campaigns/modular-addition';campaign.mkdir(parents=True)
for name in ['lock.yaml','protocol.json','PROTOCOL.md','study.json','context.json','code-manifest.json']:
    shutil.copyfile(root/'campaigns/modular-addition'/name,campaign/name)
shutil.copytree(root/'campaigns/modular-addition/materials',campaign/'materials')
for directory in sorted((root/'evidence').glob('pilot-*')):
    shutil.copytree(directory,out/'evidence'/directory.name)
for name in ['BRIEF.md','COMPUTE.md','RESOURCES.json','compute.py','materials/SOURCES.md','materials/MEASUREMENTS.md']:
    destination=out/'inputs'/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/'inputs'/name,destination)
shutil.copytree(root/'inputs/materials/openai-grok-reference',out/'inputs/materials/openai-grok-reference')
(out/'inputs/materials/wheels').symlink_to(root/'inputs/materials/wheels',target_is_directory=True)
environment=out/'.venv';venv.EnvBuilder(with_pip=True).create(environment)
py=str(environment/'bin/python')
subprocess.run([py,'-m','pip','install','--no-index','--find-links',str(root/'inputs/materials/wheels'),'torch','numpy','scipy','matplotlib'],check=True)
subprocess.run([py,'study/build.py'],cwd=out,check=True)
shutil.copyfile(out/'build/engine.dylib',campaign/'materials/engine.dylib')
(out/'reproduction-origin.json').write_text(json.dumps({'source_workspace':str(root),'new_environment':str(environment),'scientific_protocol':'campaigns/modular-addition/protocol.json','historical_pilots':'copied for provenance; a fresh qualification is also run'},indent=2))
print('Fresh offline environment staged at '+str(out))
