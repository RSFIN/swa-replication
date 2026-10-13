#!/usr/bin/env python3
from pathlib import Path
import sys,os,json,uuid,time,argparse,re
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.config import resolve_model
from src.providers import build_request,call,ProviderError
from src.benchmarks import load_benchmark
from src.plan import make_plan
from src.util import read_json,write_json_atomic,safe_model_config,sha256_text

p=argparse.ArgumentParser(); p.add_argument('--benchmarks',nargs='+',default=['crmarena','appworld']); p.add_argument('--appworld-bundle'); p.add_argument('--allow-partial',action='store_true'); a=p.parse_args()
exp=read_json(ROOT/'config/experiment.json'); cfg=resolve_model(ROOT,ROOT/'config/active_model.json'); key=os.environ.get(cfg['api_key_env'])
if not key: raise SystemExit('Missing env '+cfg['api_key_env'])
if exp.get('formal_requires_all_benchmarks_ready') and not a.allow_partial and set(a.benchmarks)!={'crmarena','appworld'}: raise SystemExit('Formal mode requires both benchmarks; use --allow-partial only for smoke testing.')
rows=[]
for b in a.benchmarks:
    ext=a.appworld_bundle if b=='appworld' else None
    try: d,rr=load_benchmark(ROOT,b,ext); rows.extend(rr)
    except Exception:
        if a.allow_partial: print('SKIP',b,'not ready'); continue
        raise
if not rows: raise SystemExit('No ready benchmark rows.')
plan=make_plan(rows,int(exp['repeats']),int(exp['run_order_seed']),cfg['run_label'])
runroot=ROOT/'results'/cfg['run_label']; (runroot/'requests').mkdir(parents=True,exist_ok=True); (runroot/'raw').mkdir(exist_ok=True); (runroot/'normalized').mkdir(exist_ok=True)
write_json_atomic(runroot/'FROZEN_MODEL_CONFIG.json',safe_model_config(cfg)); write_json_atomic(runroot/'FROZEN_EXPERIMENT_CONFIG.json',exp)
# refuse model-config drift on resume
if read_json(runroot/'FROZEN_MODEL_CONFIG.json')!=safe_model_config(cfg): raise SystemExit('Model config drift detected.')
for i,r in enumerate(plan,1):
    rid=r['run_id']; norm=runroot/'normalized'/f'{sha256_text(rid)[:16]}.json'
    if norm.exists(): continue
    prompt_path=Path(r['prompt_path'])
    if not prompt_path.is_absolute():
        # embedded package prompt, or external appworld bundle manifest-relative path
        if r['benchmark']=='appworld' and a.appworld_bundle: prompt_path=Path(a.appworld_bundle)/r['prompt_path']
        else: prompt_path=ROOT/r['prompt_path']
    prompt=prompt_path.read_text(encoding='utf-8')
    if sha256_text(prompt)!=r['prompt_sha256']: raise RuntimeError('Prompt hash mismatch '+str(prompt_path))
    reqfile=runroot/'requests'/f'{sha256_text(rid)[:16]}.json'
    if reqfile.exists(): req=read_json(reqfile); call_id=req['call_id']; body=req['body']
    else:
        call_id=str(uuid.uuid4()); body=build_request(cfg,exp['system_instruction'],prompt,call_id)
        write_json_atomic(reqfile,{'run_id':rid,'call_id':call_id,'model_config':safe_model_config(cfg),'prompt_sha256':r['prompt_sha256'],'body':body})
    maxa=int(exp['retry']['max_attempts']); base=float(exp['retry']['base_delay_seconds']); last=None
    for attempt in range(1,maxa+1):
        try:
            res=call(cfg,key,body,timeout=int(exp['timeout_seconds'])); last=None; break
        except ProviderError as e:
            last=e; msg=str(e); m=re.search(r'"status"\s*:\s*(\d+)',msg); status=int(m.group(1)) if m else None
            if status not in exp['retry']['retry_statuses'] or attempt==maxa: raise
            time.sleep(base*(2**(attempt-1)))
    rawfile=runroot/'raw'/f'{sha256_text(rid)[:16]}.json'; write_json_atomic(rawfile,res['raw'])
    rec={**r,'requested_model':cfg['model'],'response_model':res['response_model'],'finish_reason':res['finish_reason'],'latency_ms':res['latency_ms'],'request_id':res['request_id'],'usage':res['usage'],'text':res['text'],'attempts':attempt,'call_id':call_id,'prompt_chars':len(prompt)}
    write_json_atomic(norm,rec)
    print(f"[{i}/{len(plan)}] {rid} finish={res['finish_reason']} input={res['usage'].get('input_tokens')} output={res['usage'].get('output_tokens')} ms={res['latency_ms']}")
print('DONE',cfg['run_label'])
