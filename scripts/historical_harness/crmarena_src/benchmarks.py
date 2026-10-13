from pathlib import Path
from .util import load_manifest,read_json

def benchmark_dir(root,name,external=None):
    if external: return Path(external)
    return Path(root)/'benchmarks'/name

def load_benchmark(root,name,external=None):
    d=benchmark_dir(root,name,external)
    if name=='appworld':
        ready=d/'READY.json'
        if not ready.exists(): raise RuntimeError('AppWorld formal bundle is not READY. Run the local feasibility/compiler stage first.')
        r=read_json(ready)
        aud=r.get('compiler_audits') or {}
        if not aud or any(v!='PASS' for v in aud.values()): raise RuntimeError('AppWorld compiler audits not all PASS.')
    man=d/'manifest.csv'
    if not man.exists(): raise RuntimeError(f'Missing benchmark manifest: {man}')
    rows=load_manifest(man)
    if not rows or any(x.get('ready')!='1' for x in rows): raise RuntimeError(f'Benchmark {name} manifest not fully ready')
    return d,rows
