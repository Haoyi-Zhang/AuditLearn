#!/usr/bin/env python3
"""One-command complete reproduction with truthful command-level resource logs."""
from __future__ import annotations
import argparse,json,os,re,resource,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
ALIASES={
 'check':['check'],
 'pilot':['pilot'],
 'stress':['stress'],
 'scale':['scale','scaling'],
 'offgrid':['offgrid','off-grid','misspecification','robustness','robust'],
 'verify':['verify'],
 'smoke':['smoke'],
}

def commands()->set[str]:
 s=(ROOT/'run.py').read_text(errors='ignore')
 out=set(re.findall(r"add_parser\(['\"]([^'\"]+)",s))
 h=subprocess.run([sys.executable,'run.py','--help'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True).stdout
 for g in re.findall(r'\{([^{}]+)\}',h):
  out.update(x.strip() for x in g.split(',') if re.fullmatch(r'[A-Za-z0-9_-]+',x.strip()))
 return out

def choose(avail,role,required=True):
 for a in ALIASES[role]:
  if a in avail:return a
 if required:raise RuntimeError(f'missing required run.py command for {role}; available={sorted(avail)}')
 return None

def run(cmd:list[str],log:Path):
 start=time.perf_counter();cpu0=time.process_time();before=resource.getrusage(resource.RUSAGE_CHILDREN)
 with log.open('w',encoding='utf-8') as f:
  p=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,text=True)
 after=resource.getrusage(resource.RUSAGE_CHILDREN)
 return {'command':cmd,'returncode':p.returncode,'wall_seconds':time.perf_counter()-start,
         'parent_cpu_seconds':time.process_time()-cpu0,
         'child_user_seconds':after.ru_utime-before.ru_utime,'child_system_seconds':after.ru_stime-before.ru_stime,
         'maxrss_kib_process_peak':after.ru_maxrss,'log':str(log.relative_to(ROOT))}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('output',nargs='?',default='repro-results');ap.add_argument('--skip-long',action='store_true');a=ap.parse_args()
 out=(ROOT/a.output).resolve();out.mkdir(parents=True,exist_ok=True);logs=out/'command-logs';logs.mkdir(exist_ok=True)
 avail=commands();mapping={r:choose(avail,r,required=(r!='smoke')) for r in ALIASES}
 roles=['check','pilot']+([] if a.skip_long else ['stress','scale','offgrid'])+['verify']
 rec=[]
 for role in roles:
  cmd=[sys.executable,'run.py',mapping[role],'--output',str(out)]
  z=run(cmd,logs/f'{role}.log');z['role']=role;rec.append(z)
  if z['returncode']:
   (out/'reproduction-manifest.json').write_text(json.dumps({'status':'FAIL','mapping':mapping,'commands':rec},indent=2)+'\n');return z['returncode']
 if (ROOT/'report.py').exists():
  z=run([sys.executable,'report.py','--results',str(out)],logs/'report.log');z['role']='report';rec.append(z)
  if z['returncode']:
   # Older report.py may accept a positional path or no argument. Try the documented no-argument form only when it is safe.
   z2=run([sys.executable,'report.py'],logs/'report-fallback.log');z2['role']='report-fallback';rec.append(z2)
   if z2['returncode']:
    (out/'reproduction-manifest.json').write_text(json.dumps({'status':'FAIL','mapping':mapping,'commands':rec},indent=2)+'\n');return z2['returncode']
 if mapping.get('smoke'):
  smoke=out/'smoke';smoke.mkdir(exist_ok=True)
  z=run([sys.executable,'run.py',mapping['smoke'],'--output',str(smoke)],logs/'smoke.log');z['role']='smoke';rec.append(z)
  if z['returncode']:return z['returncode']
 extra=[
  [sys.executable,'reviewer_requirements.py','--results',str(out)]+(['--allow-partial'] if a.skip_long else []),
  [sys.executable,'reviewer_invariants.py','--results',str(out)],
  [sys.executable,'validate_release.py','--results',str(out),'--write-manifest'],
 ]
 for i,cmd in enumerate(extra):
  z=run(cmd,logs/f'post-{i+1}.log');z['role']=Path(cmd[1]).stem;rec.append(z)
  if z['returncode']:
   (out/'reproduction-manifest.json').write_text(json.dumps({'status':'FAIL','mapping':mapping,'commands':rec},indent=2)+'\n');return z['returncode']
 manifest={'schema_version':1,'status':'PASS','generated_utc':datetime.now(timezone.utc).isoformat(),
           'python':sys.version,'platform':sys.platform,'cpu_count':os.cpu_count(),'mapping':mapping,'commands':rec,
           'wall_seconds_sum':sum(x['wall_seconds'] for x in rec),
           'note':'maxrss values are per-process peaks reported by the host OS and are not additive.'}
 (out/'reproduction-command-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps(manifest,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
