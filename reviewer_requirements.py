#!/usr/bin/env python3
"""Semantic checks for the strengthened reviewer-facing experiment matrix."""
from __future__ import annotations
import argparse,csv,json,re,sys
from collections import defaultdict
from pathlib import Path

def values(row, aliases):
    for k in aliases:
        if k in row and row[k] not in ('',None): return row[k]
    return None

def inspect(root:Path):
    records=[]; files=[]
    for p in sorted(root.rglob('*.csv')):
        with p.open(newline='',encoding='utf-8') as f:
            r=csv.DictReader(f); rows=list(r)
        files.append({'file':str(p.relative_to(root)),'rows':len(rows),'columns':r.fieldnames or []})
        for row in rows:
            records.append((p,row))
    methods=set();seeds=set();delays=set();truths=set();campaigns=defaultdict(int); horizons=set()
    for p,row in records:
        m=values(row,['method','algorithm','selector']) or next((row[k] for k in row if any(x in k.lower() for x in ('method','algorithm','selector')) and row[k] not in ('',None)),None)
        s=values(row,['seed','random_seed']) or next((row[k] for k in row if 'seed' in k.lower() and row[k] not in ('',None)),None)
        d=values(row,['delay_mechanism','delay','audit_mechanism','scenario']) or next((row[k] for k in row if any(x in k.lower() for x in ('delay','mechanism','scenario')) and row[k] not in ('',None)),None)
        t=values(row,['truth_id','truth','model_id','true_model']) or next((row[k] for k in row if ('truth' in k.lower() or k.lower() in ('model','p_id')) and row[k] not in ('',None)),None)
        h=values(row,['horizon','T'])
        c=values(row,['campaign','experiment']) or p.stem
        if m: methods.add(m.strip())
        if s: seeds.add(s.strip())
        if d: delays.add(d.strip())
        if t: truths.add(t.strip())
        if h: horizons.add(h.strip())
        campaigns[c]+=1
    low={m.lower().replace('_','-') for m in methods}
    req={
      'has_prefix':any('prefix' in m for m in low),
      'has_completion_only':any('completion' in m and 'intersection' not in m for m in low),
      'has_intersection':any('intersection' in m for m in low),
      'has_returned_negative_control':any('returned' in m for m in low),
      'no_ambiguous_completed':not any(m in {'completed','complete','returned'} for m in low),
      'method_count_ge_8':len(methods)>=8,
      'seed_count_ge_16':len(seeds)>=16,
      'delay_count_ge_3':len(delays)>=3,
      'truth_count_ge_27':len(truths)>=27,
      'has_offgrid_file':(any(any(k in f['file'].lower() for k in ('offgrid','off-grid','misspec','robust')) for f in files) or (root/'CURATION.json').exists() and 'offgrid' in (root/'CURATION.json').read_text().lower() or any(any(k in m for k in ('robust','cover','offgrid','misspec')) for m in low)),
    }
    return {'root':str(root),'files':files,'methods':sorted(methods),'seeds':sorted(seeds),
            'delays':sorted(delays),'truths':sorted(truths),'horizons':sorted(horizons),
            'campaign_rows':dict(sorted(campaigns.items())),'requirements':req,
            'errors':[k for k,v in req.items() if not v]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True);ap.add_argument('--allow-partial',action='store_true')
    a=ap.parse_args();d=inspect(Path(a.results));
    out=Path(a.results)/'reviewer-requirements.json';out.write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'requirements':d['requirements'],'errors':d['errors']},indent=2))
    return 0 if a.allow_partial or not d['errors'] else 1
if __name__=='__main__': raise SystemExit(main())
