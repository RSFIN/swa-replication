from pathlib import Path
from _shared import *
try:
    import appworld
    from appworld import AppWorld, load_task_ids
    from appworld.common.datetime import VanillaDateTime as DateTime
except Exception as e:
    raise SystemExit('AppWorld import failed. Install official AppWorld package/data.') from e
cfg=load_cfg(); ids=set(load_task_ids(cfg['split']))
missing=[x for x in cfg['formal_instances']+cfg['design_instances'] if x not in ids]
if missing: raise SystemExit(f'Missing frozen tasks: {missing}')
if set(cfg['families'])!=set(REGISTRY): raise SystemExit('Registry/family mismatch')
print('PASS: AppWorld formal compiler preflight')
print('formal tasks:',len(cfg['formal_instances']))
