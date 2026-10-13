#!/usr/bin/env python3
from pathlib import Path
import sys,os,json,uuid
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.config import resolve_model
from src.providers import build_request,call
from src.util import safe_model_config,write_json_atomic
active=ROOT/'config/active_model.json'
if not active.exists(): raise SystemExit('Missing config/active_model.json; run prepare_active_model.py first.')
cfg=resolve_model(ROOT,active); key=os.environ.get(cfg['api_key_env'])
if not key: raise SystemExit('Missing env '+cfg['api_key_env'])
body=build_request(cfg,'You are a controlled API preflight.','Reply exactly PREFLIGHT_OK.',str(uuid.uuid4()))
r=call(cfg,key,body,timeout=120)
print('requested model:',cfg['model']); print('response model:',r['response_model']); print('finish:',r['finish_reason']); print('text:',repr(r['text'][:200])); print('usage:',r['usage'])
out=ROOT/'results'/'preflight'/f"{cfg['run_label']}.json"; write_json_atomic(out,{'model_config':safe_model_config(cfg),'response_model':r['response_model'],'finish_reason':r['finish_reason'],'usage':r['usage'],'text':r['text'][:500]})
if 'PREFLIGHT_OK' not in r['text']: raise SystemExit('Preflight content mismatch; do not start formal run.')
print('PASS preflight:',out)
