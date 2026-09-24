#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,re,shutil
from pathlib import Path

def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def csv_campaign(p):
 try:
  with p.open(newline='',encoding='utf-8') as f:
   r=csv.DictReader(f);vals=set()
   for i,row in enumerate(r):
    for k in ('campaign','experiment','scenario_family'):
     if row.get(k):vals.add(row[k].lower())
    if i>=200:break
  return ' '.join(sorted(vals))
 except:return ''

def classify(p):
 s=str(p).lower().replace('_','-')+' '+(csv_campaign(p) if p.suffix=='.csv' else '')
 if any(k in s for k in ('offgrid','off-grid','misspec','tv-cover','cover-robust')):return 'offgrid'
 if 'stress' in s:return 'stress'
 if any(k in s for k in ('scale','scaling','horizon-backlog')):return 'scale'
 if 'pilot' in s:return 'pilot'
 if any(k in s for k in ('exact','check','oracle')):return 'check'
 if any(k in s for k in ('verify','reproduction')):return 'verify'
 return 'misc'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='final-results');a=ap.parse_args();out=Path(a.output)
 sources={
  'full':Path('reviewer-full'),
  'expanded':Path('reviewer-expanded'),
  'offgrid':Path('reviewer-offgrid'),
  'fallback':Path('reviewer-results'),
 }
 priority={
  'stress':['expanded','full','fallback'],
  'offgrid':['offgrid','full','fallback'],
  'pilot':['full','fallback','expanded'],
  'scale':['full','fallback','expanded'],
  'check':['full','fallback','expanded'],
  'verify':['full','fallback','expanded'],
  'misc':['full','expanded','offgrid','fallback'],
 }
 allfiles=[]
 for sn,root in sources.items():
  if not root.exists():continue
  for p in root.rglob('*'):
   if not p.is_file():continue
   if p.name in {'reproduction-manifest.json','reviewer-requirements.json','reviewer-invariants.json','reviewer-empirical-summary.json'}:continue
   allfiles.append((sn,root,p,classify(p)))
 # Group by relative path and campaign. If generic relative names collide across distinct campaigns, namespace them.
 groups={}
 for sn,root,p,c in allfiles:
  rel=p.relative_to(root)
  key=(c,str(rel))
  groups.setdefault(key,[]).append((sn,p,root))
 selected=[]
 for (c,rel),items in groups.items():
  ranks={s:i for i,s in enumerate(priority[c])}
  items.sort(key=lambda x:(ranks.get(x[0],99),-x[1].stat().st_mtime))
  sn,p,root=items[0]
  # Campaign-specific namespace only when a relative path is shared by multiple campaigns.
  same_rel_campaigns={cc for (cc,rr) in groups if rr==rel}
  dstrel=Path(c)/rel if len(same_rel_campaigns)>1 else Path(rel)
  selected.append((c,sn,p,dstrel))
 if out.exists():shutil.rmtree(out)
 out.mkdir(parents=True)
 manifest=[]
 for c,sn,p,rel in sorted(selected,key=lambda x:str(x[3])):
  q=out/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
  manifest.append({'campaign_class':c,'source_set':sn,'source':str(p),'destination':str(rel),'bytes':q.stat().st_size,'sha256':sha(q)})
 (out/'CURATION.json').write_text(json.dumps({'schema_version':1,'sources':{k:str(v) for k,v in sources.items() if v.exists()},'files':manifest},indent=2)+'\n')
 print(json.dumps({'output':str(out),'files':len(manifest),'classes':sorted({x[0] for x in selected})},indent=2))
if __name__=='__main__':main()
