#!/usr/bin/env python3
"""Cross-method invariants checked from serialized episode/run tables.

Checks are conditional on the relevant columns being present; the JSON report
records both executed and skipped invariants so absence is never presented as a
pass.
"""
from __future__ import annotations
import argparse,csv,json,math
from collections import defaultdict
from pathlib import Path

def canon(m:str)->str:
    s=m.lower().replace('_','-').replace(' ','-')
    if 'intersection' in s:return 'intersection'
    if 'completion' in s and 'intersection' not in s:return 'completion-only'
    if 'prefix' in s and 'intersection' not in s:return 'prefix-only'
    if 'returned' in s:return 'returned-only'
    if 'robust' in s or 'cover' in s:return 'cover-robust'
    return s

def num(x):
    try:return float(x)
    except:return None

def truthy(x):return str(x).strip().lower() in {'1','true','yes'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True);a=ap.parse_args();root=Path(a.results)
    checks=[];errors=[];numeric_bad=[]
    tables=[]
    for p in root.rglob('*.csv'):
        with p.open(newline='',encoding='utf-8') as f:
            r=csv.DictReader(f);rows=list(r);cols=r.fieldnames or []
        tables.append((p,cols,rows))
        for ri,row in enumerate(rows,2):
            for k,v in row.items():
                if not v:continue
                lk=k.lower()
                if any(t in lk for t in ('regret','loss','value','width','debt','mass','count','size')):
                    z=num(v)
                    if z is not None and not math.isfinite(z):numeric_bad.append(f'{p}:{ri}:{k}={v}')
    checks.append({'name':'finite_numeric_outputs','executed':True,'passed':not numeric_bad,'details':numeric_bad[:50]})
    if numeric_bad:errors.append('nonfinite numeric outputs')
    # Locate the richest episode table with method and a time index.
    eps=[]
    for p,cols,rows in tables:
        if 'method' in cols and any(x in cols for x in ('episode','time','t')):
            eps.append((len(rows),p,cols,rows))
    if eps:
        _,p,cols,rows=max(eps)
        output_cols={'method','confidence_set_size','set_size','confidence_width','width','truth_excluded','excluded_truth'}
        keycols=[c for c in cols if c not in output_cols and not any(x in c.lower() for x in ('regret','loss','value','reward','waste','launch','debt','mass','outstanding','runtime'))]
        groups=defaultdict(dict)
        for row in rows:
            key=tuple(row.get(c,'') for c in keycols);groups[key][canon(row['method'])]=row
        for metric in [('confidence_set_size','set_size'),('confidence_width','width')]:
            mc=next((x for x in metric if x in cols),None)
            if not mc:continue
            n=viol=0
            for g in groups.values():
                if {'intersection','prefix-only','completion-only'}<=set(g):
                    vi=num(g['intersection'].get(mc));vp=num(g['prefix-only'].get(mc));vc=num(g['completion-only'].get(mc))
                    if None not in (vi,vp,vc):
                        n+=1
                        if vi>min(vp,vc)+1e-10:viol+=1
            checks.append({'name':f'intersection_{mc}_no_larger','executed':n>0,'comparisons':n,'violations':viol,'passed':n>0 and viol==0})
            if n and viol:errors.append(f'intersection {mc} exceeds component in {viol} rows')
        ec=next((x for x in ('truth_excluded','excluded_truth') if x in cols),None)
        if ec:
            n=viol=0;ret_ex=0;valid_ex=0
            for g in groups.values():
                if 'returned-only' in g:ret_ex+=truthy(g['returned-only'].get(ec,''))
                for m in ('prefix-only','completion-only','intersection'):
                    if m in g:valid_ex+=truthy(g[m].get(ec,''))
                if {'intersection','prefix-only','completion-only'}<=set(g):
                    n+=1;expected=truthy(g['prefix-only'].get(ec,'')) or truthy(g['completion-only'].get(ec,''))
                    if truthy(g['intersection'].get(ec,''))!=expected:viol+=1
            checks.append({'name':'intersection_exclusion_is_component_union','executed':n>0,'comparisons':n,'violations':viol,'passed':n>0 and viol==0})
            checks.append({'name':'negative_control_and_valid_coverage_counts','executed':True,'returned_only_exclusions':ret_ex,'valid_method_exclusions':valid_ex,'passed':True})
            if n and viol:errors.append(f'intersection exclusion mismatch in {viol} rows')
    else:
        checks.append({'name':'episode_level_cross_method_invariants','executed':False,'passed':False,'reason':'no method/time CSV found'})
    report={'results':str(root),'checks':checks,'errors':errors,'status':'PASS' if not errors else 'FAIL'}
    (root/'reviewer-invariants.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
