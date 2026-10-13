from pathlib import Path
from .util import read_json

def resolve_model(root,active_path):
    root=Path(root); active=read_json(active_path); presets=read_json(root/'config/model_presets.json')
    name=active['preset']
    if name not in presets: raise KeyError(f'Unknown preset {name}')
    cfg=dict(presets[name]); cfg.update(active.get('override') or {})
    cfg['preset']=name; cfg['run_label']=active.get('run_label') or name
    return cfg
