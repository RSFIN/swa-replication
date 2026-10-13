#!/usr/bin/env python3
from pathlib import Path
import sys,json,csv,argparse,re
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.util import read_json
from src.eval_crmarena import evaluate as eval_crm
p=argparse.ArgumentParser(); p.add_argument('run_label'); p.add_argument('--appworld-bundle'); a=p.parse_args()
runroot=ROOT/'results'/a.run_label; rows=[]
crm=read_json(ROOT/'benchmarks/crmarena/sealed/stage_oracle.json')
apporacle=None
if a.appworld_bundle:
    op=Path(a.appworld_bundle)/'sealed/oracle.json'
    if op.exists(): apporacle=read_json(op)
for f in sorted((runroot/'normalized').glob('*.json')):
    r=read_json(f); ev={}
    if r['benchmark']=='crmarena': ev=eval_crm(r['text'],crm[r['task_id']])
    elif r['benchmark']=='appworld':
        if apporacle is None: ev={'correct':'','predicted':'','gold':'','protocol_ok':'','auto_failure_class':'NEEDS_NATIVE_APPWORLD_EVAL'}
        else:
            # Local compiler may provide normalized answer plus optional accepted variants.
            o=apporacle[r['task_id']]; ans=r['text'].strip(); accepted=[str(x).strip() for x in o.get('accepted_answers',[o.get('answer','')])]
            ev={'correct':int(ans in accepted),'predicted':ans,'gold':'<LOCAL_PROTECTED>','protocol_ok':1,'auto_failure_class':'E0' if ans in accepted else 'APPWORLD_INCORRECT'}
    u=r.get('usage') or {}
    rows.append({
      'run_id':r['run_id'],'model_label':r['model_label'],'requested_model':r['requested_model'],'response_model':r['response_model'],
      'benchmark':r['benchmark'],'task_id':r['task_id'],'native_task_id':r['native_task_id'],'condition':r['condition'],'repeat_id':r['repeat_id'],
      'correct':ev.get('correct',''),'predicted':ev.get('predicted',''),'gold':ev.get('gold',''),'protocol_ok':ev.get('protocol_ok',''),'auto_failure_class':ev.get('auto_failure_class',''),
      'target_issue_correct':ev.get('target_issue_correct',''),'target_product_correct':ev.get('target_product_correct',''),'issue_stage_correct':ev.get('issue_stage_correct',''),'product_stage_correct':ev.get('product_stage_correct',''),'workload_stage_correct':ev.get('workload_stage_correct',''),
      'input_tokens':u.get('input_tokens',''),'cached_input_tokens':u.get('cached_input_tokens',''),'output_tokens':u.get('output_tokens',''),'reasoning_tokens':u.get('reasoning_tokens',''),'latency_ms':r['latency_ms'],'finish_reason':r['finish_reason'],'attempts':r['attempts'],'prompt_chars':r['prompt_chars']})
fields=list(rows[0]) if rows else []
out=runroot/'evaluated.csv'
with open(out,'w',encoding='utf-8',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(rows)
print('Wrote',out,'rows',len(rows))
