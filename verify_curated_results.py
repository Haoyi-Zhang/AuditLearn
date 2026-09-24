#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from collections import Counter
from pathlib import Path
ALLOWED_GENERATED={'CURATION.json','reviewer-requirements.json','reviewer-invariants.json','reviewer-empirical-summary.json','reproduction-manifest.json','reproduction-command-manifest.json','curated-verification.json','negative-integrity-tests.json'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',default='results');a=ap.parse_args();root=Path(a.results)
 errors=[];p=root/'CURATION.json'
 if not p.exists():errors.append('CURATION.json missing');manifest={'files':[]}
 else:
  try:manifest=json.loads(p.read_text())
  except Exception as e:errors.append(f'cannot parse CURATION.json: {e}');manifest={'files':[]}
 records=manifest.get('files',[]);dests=[r.get('destination') for r in records]
 dup=[x for x,n in Counter(dests).items() if x and n>1]
 if dup:errors.append('duplicate manifest destinations: '+', '.join(dup))
 classes={r.get('campaign_class') for r in records}
 required={'check','pilot','stress','scale','offgrid'}
 if not required<=classes:errors.append('missing campaign classes: '+', '.join(sorted(required-classes)))
 expected=set()
 for r in records:
  rel=r.get('destination');
  if not rel:errors.append('manifest record without destination');continue
  expected.add(rel);q=root/rel
  if not q.exists():errors.append(f'missing curated file: {rel}');continue
  got=sha(q)
  if got!=r.get('sha256'):errors.append(f'hash mismatch: {rel}')
  if q.stat().st_size!=r.get('bytes'):errors.append(f'byte-size mismatch: {rel}')
  if q.suffix=='.csv':
   with q.open(newline='',encoding='utf-8') as f:
    rr=csv.reader(f);header=next(rr,None);seen=set();duprows=0
    for row in rr:
     t=tuple(row)
     if t in seen:duprows+=1
     seen.add(t)
   if duprows:errors.append(f'exact duplicate rows in {rel}: {duprows}')
 actual=set()
 for q in root.rglob('*'):
  if q.is_file() and q.name not in ALLOWED_GENERATED:actual.add(str(q.relative_to(root)))
 extra=actual-expected
 if extra:errors.append('unmanifested result files: '+', '.join(sorted(extra)[:30]))
 report={'status':'PASS' if not errors else 'FAIL','manifest_files':len(records),'classes':sorted(x for x in classes if x),'errors':errors}
 (root/'curated-verification.json').write_text(json.dumps(report,indent=2)+'\n') if root.exists() else None
 print(json.dumps(report,indent=2));return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
