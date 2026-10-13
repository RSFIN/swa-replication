from __future__ import annotations
import sys,json,csv,hashlib,inspect,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from swa_appworld.common import CompilerRuntime,family_id,sha256_obj
from swa_appworld.registry import REGISTRY
from swa_appworld.render import SYSTEM,render

def load_cfg(): return json.loads((ROOT/'config/formal_sample.json').read_text(encoding='utf-8'))
def sha_text(t): return hashlib.sha256(t.encode('utf-8')).hexdigest()
