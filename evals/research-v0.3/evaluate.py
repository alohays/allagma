"""Frozen, local three-task comparison controller using the public workspace API."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import random
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from allagma import bundles,research
from allagma.files import file_hash,inventory,read_json,utcnow,write_json

BASE=ROOT/'evals/research-v0.3'
WORK=ROOT/'work/v03-evaluation'
TASKS=('core-culp','ema-schedule','modular-addition')
CODEX=Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex')


def native_settings():
    return research._load('evaluation_native',ROOT/'adapters/codex/session.py').selected_settings(Path.home()/'.codex/config.toml')


def assemble_materials(task,destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    wheelhouse=ROOT/'work/v03-development'/('wheelhouse-core' if task=='core-culp' else 'wheelhouse-torch')
    shutil.copytree(wheelhouse,destination/'wheels')
    if task=='core-culp':
        source=ROOT/'studies/core-culp/reference'
        for name in ('code','data','metadata'):
            shutil.copytree(source/name,destination/'capsule-6460826'/name)
        (destination/'capsule-6460826/code/run.sh').unlink()
        reference=read_json(source/'controller-task.json')
        prompt=read_json(source/'upstream-prompts.json')['codeocean_hard']
        (destination/'task.txt').write_text(prompt.replace('{task_prompt}',reference['task_prompt']).replace('{json_fields}',str(reference['results'][0].keys()))+'\n')
        source_note=('CORE-Bench public training capsule capsule-6460826, CULP. Benchmark commit '
            'e32a2980e72fe6eb04ee04eb749458f570625663. Capsule DOI '+reference['capsule_doi']+'.\n'
            'Original results, scorer, reference answers, environment and reproduction instructions are excluded. '
            'This local selected-task evaluation supplies an offline package wheelhouse and adds evidence/review requirements; it is not a leaderboard run.\n')
    elif task=='ema-schedule':
        source=ROOT/'studies/ema-2d-diffusion'
        prior=destination/'prior-study';prior.mkdir()
        for name in ('science.py','runner.py'):
            shutil.copyfile(source/'domain'/name,prior/name)
        shutil.copyfile(source/'publication/v2/manuscript.md',prior/'prior-report.md')
        shutil.copyfile(source/'REFERENCE.md',prior/'REFERENCE.md')
        shutil.copyfile(source/'reference/LICENSE',prior/'LICENSE')
        shutil.copyfile(source/'requirements.lock',destination/'requirements-reference.lock')
        source_note=('Prior study: Allagma studies/ema-2d-diffusion at repository commit 6d2daf0. '
            'Scientific implementation derives from SakanaAI/AI-Scientist commit 1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb. '
            'The prior report is context; its historical evidence links are not current confirmation data. '
            'The old runner contains study-specific orchestration and budget guards: adapt its scientific mechanism to this brief and the common broker. '
            'Do not reuse its old trajectories or confirmation outputs.\n'
            'Retain the supplied AI Scientist Source Code License and prominently disclose AI-generated/adapted code and reporting.\n')
    else:
        source=ROOT/'work/v03-development/grok'
        target=destination/'openai-grok-reference';target.mkdir()
        for name in ('README.md','LICENSE'):
            shutil.copyfile(source/name,target/name)
        shutil.copytree(source/'grok',target/'grok',ignore=shutil.ignore_patterns('__pycache__'))
        source_note=('Reference: Power et al. (2022), Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets, '
            'https://arxiv.org/abs/2201.02177. Code: https://github.com/openai/grok at '
            '3d64b1d8c1d595dd8ebdb7771998823f1b14c7b3, with its MIT license. '
            'The brief specifies a bounded MLP adaptation, not replication of the original transformer code or training horizons.\n')
    (destination/'SOURCES.md').write_text('# Supplied source materials\n\n'+source_note+
        '\nThe wheelhouse is `inputs/materials/wheels` after preparation. Install inside a study-owned environment. '
        'First imports in a fresh environment can take tens of seconds on this host; retain failures and choose timeouts within the supplied profile.\n')
    shutil.copyfile(BASE/'MEASUREMENTS.md',destination/'MEASUREMENTS.md')
    return inventory(destination)


def freeze():
    for command in (['git','diff','--quiet'],['git','diff','--cached','--quiet']):
        if subprocess.run(command,cwd=ROOT).returncode:raise ValueError('Commit tracked changes before freezing')
    destination=BASE/'frozen'
    if destination.exists():raise ValueError('Freeze already exists; do not overwrite a comparison')
    destination.mkdir()
    inputs={}
    for task in TASKS:
        inputs[task]=assemble_materials(task,WORK/'materials'/task)
    paths=set(bundles.source_inventory(ROOT))
    paths.update(str(p.relative_to(ROOT)) for p in (BASE/'briefs').glob('*.md'))
    paths.update('evals/research-v0.3/'+name for name in ('CRITERIA.md','MEASUREMENTS.md','profiles.json','evaluate.py','score.py','test_score.py'))
    paths.update('studies/core-culp/reference/'+name for name in ('controller-task.json','upstream-evaluations.py'))
    paths.add('studies/ema-2d-diffusion/domain/science.py')
    control={name:file_hash(ROOT/name) for name in sorted(paths)}
    for name in control:
        target=destination/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    blocks=[(task,replicate) for task in TASKS for replicate in (1,2)]
    generator=random.Random(20261008);generator.shuffle(blocks)
    first=['plain','allagma']*3;generator.shuffle(first)
    order=[]
    for index,((task,replicate),initial) in enumerate(zip(blocks,first)):
        for condition in (initial,'allagma' if initial=='plain' else 'plain'):
            order.append({'run_id':f'r{len(order)+1:02d}','task':task,'replicate':replicate,'condition':condition})
    value={'frozen_at':utcnow(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'controller_files':control,'materials':inputs,'run_order':order,'settings':native_settings(),
        'cli_version':subprocess.check_output([str(CODEX),'--version'],text=True).strip(),'cli_sha256':file_hash(CODEX),
        'profiles':read_json(BASE/'profiles.json'),'final_runs':12,
        'environment':{'platform':platform.platform(),'python':platform.python_version(),'machine':platform.machine(),
                       'hardware':subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string','hw.memsize','hw.physicalcpu','hw.logicalcpu'],text=True).splitlines()},
        'scope':'Three selected task families, two conditions, two fresh sessions per condition'}
    write_json(destination/'freeze.json',value,immutable=True)
    return value


def verify_freeze():
    value=read_json(BASE/'frozen/freeze.json')
    for name,sha in value['controller_files'].items():
        if file_hash(ROOT/name)!=sha:raise ValueError('Frozen source changed: '+name)
    if native_settings()!=value['settings'] or file_hash(CODEX)!=value['cli_sha256']:
        raise ValueError('Model/settings or CLI differ from the frozen comparison')
    return value


def prepare_run(run_id):
    frozen=verify_freeze();run=next(r for r in frozen['run_order'] if r['run_id']==run_id)
    material=WORK/'materials'/run['task']
    if inventory(material)!=frozen['materials'][run['task']]:raise ValueError('Frozen materials changed')
    workspace=WORK/'runs'/run_id/'candidate';control=BASE/'runs'/run_id
    value=research.prepare(ROOT,workspace,control,brief=BASE/'briefs'/(run['task']+'.md'),
        materials=material,profile=frozen['profiles']['profiles'][run['task']],study_id=run_id,
        install_workflow=run['condition']=='allagma')
    write_json(control/'assignment.json',{**run,'freeze_sha256':file_hash(BASE/'frozen/freeze.json')},immutable=True)
    return value


def launch_run(run_id):
    frozen=verify_freeze();control=BASE/'runs'/run_id;prepared=read_json(control/'prepared.json')
    prompt=('Complete inputs/BRIEF.md from the supplied materials, resource profile and common computation interface. '
        'Read inputs/COMPUTE.md, inputs/RESOURCES.json and inputs/materials/SOURCES.md; scientific tasks also define '
        'their measurement interchange in inputs/materials/MEASUREMENTS.md. Work autonomously through planning, '
        'implementation, actual execution, recovery, critique, reporting and verification. All setup and scientific '
        'computation must use the local broker. No task-specific follow-up guidance is planned. '
        'Deliver the requested artifacts and an honest completion assessment.\n')
    result=research.run(prepared['study'],control,codex=CODEX,timeout=frozen['profiles']['native_wall_seconds'],
        session_id='evaluation',config=Path.home()/'.codex/config.toml',auth=Path.home()/'.codex/auth.json',
        interrupt_first_attempt=True,prompt=prompt)
    observations=result.get('model_observations',[])
    model_match=bool(observations) and all(item.get('model')==frozen['settings']['model'] and
        item.get('effort')==frozen['settings'].get('model_reasoning_effort') for item in observations)
    write_json(control/'outcome.json',{'native_status':result['status'],'submission_exists':(Path(prepared['study'])/'submission.json').exists(),
        'common_inputs_unchanged':inventory(Path(prepared['study'])/'inputs')==prepared['common_inputs'],
        'observed_model_settings_match':model_match,'runtime_settings_unchanged':result['settings_unchanged'],
        'fresh_single_session':len(result['thread_ids'])==1,
        'task_completion':'unscored','subsequent_coordinator_messages':0},immutable=True)
    print(json.dumps({'run_id':run_id,'status':result['status'],'thread_ids':result['thread_ids']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['freeze','verify','prepare','run'])
    parser.add_argument('--run-id');args=parser.parse_args()
    if args.operation=='freeze':print(json.dumps(freeze()['run_order'],indent=2))
    elif args.operation=='verify':print(json.dumps({'status':'pass','runs':verify_freeze()['run_order']}))
    elif args.operation=='prepare':print(json.dumps(prepare_run(args.run_id),indent=2))
    else:launch_run(args.run_id)
