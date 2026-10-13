#!/usr/bin/env python3
from pathlib import Path
import csv,statistics,random,math
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for p in (ROOT/'results').glob('*/evaluated.csv'):
    rows.extend(list(csv.DictReader(open(p,encoding='utf-8'))))
if not rows: raise SystemExit('No evaluated.csv files.')
def n(x):
    try:return float(x)
    except:return None
def mean(xs): return sum(xs)/len(xs) if xs else None
conds=['B0_RUNTIME_HEAVY','B1_TASK_LOCALIZED','B2_DECISION_SUFFICIENT']
models=sorted(set(r['model_label'] for r in rows)); benches=sorted(set(r['benchmark'] for r in rows))
summary=[]
for m in models:
  for b in benches:
    for c in conds:
      rr=[r for r in rows if r['model_label']==m and r['benchmark']==b and r['condition']==c]
      if not rr: continue
      acc=[n(r['correct']) for r in rr if n(r['correct']) is not None]
      def med(k):
        x=[n(r[k]) for r in rr if n(r[k]) is not None]; return statistics.median(x) if x else None
      summary.append({'model':m,'benchmark':b,'condition':c,'n':len(rr),'accuracy':mean(acc),'median_input_tokens':med('input_tokens'),'median_reasoning_tokens':med('reasoning_tokens'),'median_latency_ms':med('latency_ms')})
with open(ROOT/'results'/'aggregate_summary.csv','w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
# paired task/model contrasts using repeat-averaged accuracy
contr=[]
for m in models:
  for b in benches:
    tids=sorted(set(r['task_id'] for r in rows if r['model_label']==m and r['benchmark']==b))
    vals={}
    for t in tids:
      for c in conds:
        x=[n(r['correct']) for r in rows if r['model_label']==m and r['benchmark']==b and r['task_id']==t and r['condition']==c and n(r['correct']) is not None]
        if x: vals[(t,c)]=mean(x)
    for a,c in [(conds[0],conds[1]),(conds[1],conds[2]),(conds[0],conds[2])]:
      dif=[vals[(t,c)]-vals[(t,a)] for t in tids if (t,c) in vals and (t,a) in vals]
      if not dif: continue
      rng=random.Random(20261002); boots=[]
      for _ in range(10000):
        samp=[rng.choice(dif) for __ in dif]; boots.append(mean(samp))
      boots.sort(); lo=boots[int(.025*len(boots))]; hi=boots[int(.975*len(boots))-1]
      contr.append({'model':m,'benchmark':b,'contrast':c+' - '+a,'n_tasks':len(dif),'effect_pp':mean(dif)*100,'ci95_lo_pp':lo*100,'ci95_hi_pp':hi*100})
with open(ROOT/'results'/'paired_contrasts.csv','w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(contr[0]));w.writeheader();w.writerows(contr)
print('Wrote aggregate_summary.csv and paired_contrasts.csv')
