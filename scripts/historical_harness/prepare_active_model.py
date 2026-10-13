#!/usr/bin/env python3
from pathlib import Path
import argparse,json,shutil
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('preset'); p.add_argument('--run-label'); a=p.parse_args()
pres=json.loads((ROOT/'config/model_presets.json').read_text())
if a.preset not in pres: raise SystemExit('Unknown preset. Choices: '+', '.join(pres))
out={'preset':a.preset,'run_label':a.run_label or a.preset,'override':{}}
(ROOT/'config/active_model.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print('Wrote config/active_model.json for',a.preset)
print('API key must be exported as environment variable:',pres[a.preset]['api_key_env'])
