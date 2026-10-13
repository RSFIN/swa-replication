"""Wall-clock parent: this process never instantiates AppWorld."""
from __future__ import annotations
from _shared import *
import os
import shutil
import time
from swa_appworld.timing import measure_process


def main():
    cfg = load_cfg(); output = ROOT / 'LOCAL_ONLY_OUTPUT'; comp = output / 'compiled'
    if comp.exists(): shutil.rmtree(comp)
    for folder in ['prompts', 'contexts', 'sealed', 'worker_results', 'worker_logs']:
        (comp / folder).mkdir(parents=True, exist_ok=True)
    manifest = []; started = time.perf_counter_ns()
    for tid in cfg['formal_instances']:
        for condition in cfg['conditions']:
            key = f'{tid}_{condition}'
            command = [sys.executable, str(ROOT / 'scripts/_compile_worker.py'), tid, condition, str(comp)]
            with (comp / 'worker_logs' / (key + '.log')).open('w', encoding='utf-8') as log:
                result, elapsed_ms = measure_process(command, stdout=log, stderr=log, cwd=str(ROOT), timeout=180)
            if result.returncode != 0: raise SystemExit(f'Compiler worker failed: {key}; see worker_logs')
            row = json.loads((comp / 'worker_results' / (key + '.json')).read_text(encoding='utf-8'))
            row.update(compiler_ms=round(elapsed_ms, 3), latency_scope='cold_end_to_end_subprocess_wall_clock',
                       clock_source='parent_perf_counter_ns', parent_pid=os.getpid())
            manifest.append(row)
            print(key, f'{elapsed_ms:.3f} ms', f"{row['rendered_prompt_chars']} rendered chars", flush=True)
    with (comp / 'manifest.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(manifest[0])); writer.writeheader(); writer.writerows(manifest)
    (comp / 'SYSTEM_PROMPT.txt').write_text(SYSTEM, encoding='utf-8')
    inputs = {}
    for folder in ['scripts', 'swa_appworld', 'config', 'docs', 'schemas', 'tests']:
        for file in (ROOT / folder).rglob('*'):
            if file.is_file() and '__pycache__' not in file.parts:
                inputs[str(file.relative_to(ROOT))] = hashlib.sha256(file.read_bytes()).hexdigest()
    for name in ['README.md', 'VERSION_MANIFEST.json']:
        inputs[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    (comp / 'source_hashes.json').write_text(json.dumps(inputs, indent=2), encoding='utf-8')
    measured = {'clock': 'parent_perf_counter_ns', 'parent_pid': os.getpid(), 'conditions_measured_separately': True,
                'compiler_ms_sum': sum(float(row['compiler_ms']) for row in manifest),
                'batch_wall_ms': (time.perf_counter_ns() - started) / 1_000_000,
                'scope': 'Cold subprocess launch/import, AppWorld setup, public API collection, selected treatment construction, rendering, file writes and teardown. Auditing, native evaluation, packaging and LLM time excluded.'}
    (comp / 'latency_measurement.json').write_text(json.dumps(measured, indent=2), encoding='utf-8')
    print('WROTE', comp, 'contexts', len(manifest))
