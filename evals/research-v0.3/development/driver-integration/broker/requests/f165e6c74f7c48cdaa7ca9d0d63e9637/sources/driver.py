import subprocess,sys
subprocess.run([sys.executable,'inputs/compute.py','--label','known-answer','--timeout','2','--',sys.executable,'-c','print(2+2)'],check=True)
