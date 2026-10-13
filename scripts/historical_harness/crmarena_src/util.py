from pathlib import Path
import json,hashlib,csv,os,tempfile

def sha256_text(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def read_json(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write_json_atomic(p,obj):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=p.name+'.',dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(obj,f,ensure_ascii=False,indent=2)
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def load_manifest(p):
    with open(p,encoding='utf-8',newline='') as f: return list(csv.DictReader(f))
def safe_model_config(cfg):
    return {k:v for k,v in cfg.items() if 'key' not in k.lower() or k=='api_key_env'}
