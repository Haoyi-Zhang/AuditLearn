#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,math,statistics,re
from collections import defaultdict
from pathlib import Path

def q(xs,p):
    if not xs:return float('nan')
    y=sorted(xs);x=(len(y)-1)*p;i=int(math.floor(x));j=min(i+1,len(y));
    return y[i] if i==j else y[i]+(x-i)*(y[j]-y[i])

def pick(row,names):
    for n in names:
        if n in row and row[n] not in ('',None):return row[n]
    return None

def fnum(x):
    try:return float(x)
    except:return None

def esc(s):
    return str(s).replace('\\','\\textbackslash{}').replace('_','\\_').replace('&','\\&').replace('%','\\%').replace('#','\\#')

def read_all(root):
    tables=[]
    for p in sorted(root.rglob('*.csv')):
        try:
            with p.open(newline='',encoding='utf-8') as f:
                r=csv.DictReader(f);rows=list(r);cols=r.fieldnames or []
        except Exception:continue
        tables.append((p,cols,rows))
    return tables

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True);ap.add_argument('--paper-dir',required=True);a=ap.parse_args()
    root=Path(a.results);tabs=read_all(root)
    # Prefer run-level tables: method + seed + truth + cumulative regret, without episode/time.
    candidates=[]
    regret_alias=['pseudo_regret','cumulative_regret','regret','total_regret']
    for p,cols,rows in tabs:
        hasm='method' in cols;hass=any(x in cols for x in ('seed','random_seed'));hast=any(x in cols for x in ('truth','truth_id','true_model','model_id'))
        rc=next((x for x in regret_alias if x in cols),None)
        episode=any(x in cols for x in ('episode','time','t'))
        if hasm and hass and hast and rc:
            score=(not episode,len(rows),-len(cols));candidates.append((score,p,cols,rows,rc))
    candidates.sort(reverse=True,key=lambda x:x[0])
    selected=[]
    # Include all non-episode candidate tables, deduplicated by path.
    for c in candidates:
        if c[0][0]:selected.append(c)
    if not selected and candidates:selected=[candidates[0]]
    records=[]
    for _,p,cols,rows,rc in selected:
        for row in rows:
            v=fnum(row.get(rc));
            if v is None:continue
            rr=dict(row);rr['_regret']=v;rr['_source']=str(p.relative_to(root));records.append(rr)
    methods=defaultdict(list);exclusions=defaultdict(lambda:[0,0])
    for r in records:
        m=r.get('method','unknown');methods[m].append(r['_regret'])
        ex=pick(r,['truth_excluded','excluded_truth','cover_excluded'])
        if ex is not None:
            exclusions[m][1]+=1
            if str(ex).strip().lower() in {'1','true','yes'}:exclusions[m][0]+=1
    summaries=[]
    for m,xs in sorted(methods.items()):
        summaries.append({'method':m,'n':len(xs),'mean':statistics.fmean(xs),'median':statistics.median(xs),'q90':q(xs,.9),'max':max(xs),'excluded':exclusions[m][0],'coverage_n':exclusions[m][1]})
    # Pair methods on all shared identifiers except outputs.
    id_alias=['campaign','truth','truth_id','true_model','model_id','seed','random_seed','delay','delay_mechanism','scenario','horizon','blocker_count','audit_lag']
    maps=defaultdict(dict)
    for r in records:
        key=tuple((k,r[k]) for k in id_alias if k in r and r[k] not in ('',None)) + (('_source',r['_source']),)
        maps[r.get('method','unknown')][key]=r['_regret']
    def findmeth(token,exclude=()):
        for m in maps:
            lm=m.lower()
            if token in lm and not any(e in lm for e in exclude):return m
        return None
    inter=findmeth('intersection');prefix=findmeth('prefix',('intersection',));completion=findmeth('completion',('intersection',))
    pairs=[]
    for b in [prefix,completion]:
        if inter and b:
            ks=set(maps[inter])&set(maps[b]);diff=[maps[inter][k]-maps[b][k] for k in ks]
            if diff:
                tol=1e-12;pairs.append({'a':inter,'b':b,'n':len(diff),'wins':sum(d<-tol for d in diff),'ties':sum(abs(d)<=tol for d in diff),'losses':sum(d>tol for d in diff),'mean_diff':statistics.fmean(diff),'median_diff':statistics.median(diff)})
    # Inventory over all tables.
    inventory={'csv_files':len(tabs),'csv_rows':sum(len(x[2]) for x in tabs),'run_records':len(records),'methods':summaries,'pairs':pairs,'selected_tables':[str(c[1].relative_to(root)) for c in selected]}
    out=root/'reviewer-empirical-summary.json';out.write_text(json.dumps(inventory,indent=2)+'\n')
    pdir=Path(a.paper_dir);g=pdir/'generated';g.mkdir(exist_ok=True)
    lines=['% Generated directly from frozen run-level CSV files.','\\begin{table}[t]','\\centering','\\small','\\caption{Reviewer-facing run-level summary. Truth grids are finite benchmark populations; seeds quantify Monte Carlo variation.}','\\label{tab:reviewer-summary}','\\begin{tabular}{lrrrrr}','\\hline','Method & Runs & Mean & Median & 90th pct. & Worst \\\\','\\hline']
    for z in summaries:
        lines.append(f"{esc(z['method'])} & {z['n']} & {z['mean']:.3f} & {z['median']:.3f} & {z['q90']:.3f} & {z['max']:.3f} \\\\")
    lines+=['\\hline','\\end{tabular}','\\end{table}']
    (g/'reviewer_empirical_summary.tex').write_text('\n'.join(lines)+'\n')
    sent=[]
    if pairs:
        for z in pairs:
            sent.append(f"Across {z['n']} paired cells, {esc(z['a'])} versus {esc(z['b'])} records {z['wins']}/{z['ties']}/{z['losses']} lower/equal/higher-regret outcomes, with mean paired difference {z['mean_diff']:.3f}.")
    else:sent.append('Run-level paired summaries are recorded in the artifact; no unmatched-cell comparison is treated as paired evidence.')
    (g/'reviewer_empirical_sentence.tex').write_text('% Generated from frozen CSVs.\n'+' '.join(sent)+'\n')
    print(json.dumps(inventory,indent=2))
if __name__=='__main__':main()
