#!/usr/bin/env python3
from pathlib import Path
import sys,hashlib,csv,json
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.util import load_manifest,read_json
m=load_manifest(ROOT/'benchmarks/crmarena/manifest.csv')
assert len(m)==30
for r in m:
    p=ROOT/r['prompt_path']; assert p.exists(),p
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['prompt_sha256'],p
    txt=p.read_text(encoding='utf-8')
    assert 'OUTPUT CONTRACT' in txt and 'Return only the Id of the agent.' not in txt
oracle=read_json(ROOT/'benchmarks/crmarena/sealed/stage_oracle.json'); assert len(oracle)==10
pres=read_json(ROOT/'config/model_presets.json'); assert len(pres)==5
print('PASS: formal direct-API package validated.')
print('CRMArena: 10 tasks x 3 SCB placements = 30 frozen prompts.')
print('AppWorld: runner contract ready; local protected-data bundle still required before formal two-benchmark execution.')
