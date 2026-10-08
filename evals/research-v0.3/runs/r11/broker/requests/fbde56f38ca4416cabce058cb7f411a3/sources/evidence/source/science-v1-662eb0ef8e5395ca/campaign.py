"""Serial broker client orchestration only: no numerical work in this process."""
import json, subprocess, sys
from pathlib import Path

def main():
    assert Path('freeze.json').is_file(), 'Freeze before confirmation'
    protocol=json.loads(Path('protocol.json').read_text())
    for dataset,seeds in protocol['confirmation_seeds'].items():
        for seed in seeds:
            for policy,total in [('constant',10000),('cosine',5000),('cosine',10000)]:
                label=f'confirm-{dataset}-{seed}-{policy}-{total}'
                result_path=Path('evidence/attempts')/label/'result.json'
                if result_path.exists():
                    prior=json.loads(result_path.read_text());assert prior['status']=='completed' and prior['last_update']==total
                    print(json.dumps(dict(label=label,status='previously completed; no duplicate run')),flush=True)
                    continue
                command=[sys.executable,'inputs/compute.py','--category','compute','--label',label,'--timeout','60','--',
                         '.venv/bin/python','study.py','--phase','confirmation','--dataset',dataset,'--seed',str(seed),
                         '--policy',policy,'--total',str(total),'--stop',str(total),'--attempt-id',label]
                print(json.dumps(dict(label=label,status='submitted')),flush=True)
                result=subprocess.run(command,text=True,capture_output=True)
                try:receipt=json.JSONDecoder().raw_decode(result.stdout)[0]
                except Exception:
                    print(result.stdout,flush=True);print(result.stderr,file=sys.stderr,flush=True);raise
                print(json.dumps(dict(label=label,request_id=receipt.get('request_id'),
                      result=receipt.get('result'),injected_interruption=receipt.get('injected_interruption'))),flush=True)
                if result.returncode:
                    print(result.stdout,flush=True);print(result.stderr,file=sys.stderr,flush=True)
                    raise RuntimeError('Broker request failed; inspect existing request and artifacts before recovery')

if __name__=='__main__':main()
