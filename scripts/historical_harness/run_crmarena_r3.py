#!/usr/bin/env python3
"""CRMArena round-3 (third independent repeat) runner. Reuses r1/r2, only runs repeat_id==3
(90 calls = 3 models x 10 tasks x 3 conditions), with the 300s SLA hard budget: a call
exceeding 300s is recorded as finish_reason=timeout with no retry. Writes to a separate
results/<preset>_run3/ directory so the three runs stay separable."""
from pathlib import Path
import sys, os, json, uuid, time, re, threading
import requests
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.providers import build_request, call, ProviderError
from src.benchmarks import load_benchmark
from src.plan import make_plan
from src.util import read_json, write_json_atomic, safe_model_config, sha256_text

exp = read_json(ROOT / 'config/experiment.json')
presets = read_json(ROOT / 'config/model_presets.json')
MODELS = ['deepseek_v4_pro_0813', 'doubao_seed_2_1_lite_260915', 'qwen3_8_max_0902']
ENV_OF = {
    'deepseek_v4_pro_0813': 'DEEPSEEK_API_KEY',
    'doubao_seed_2_1_lite_260915': 'ARK_API_KEY',
    'qwen3_8_max_0902': 'DASHSCOPE_API_KEY',
}
MAX_OUT = 120000
TIMEOUT = 300
REP = 3
retry_statuses = set(exp['retry']['retry_statuses'])


def run_model(preset):
    cfg = dict(presets[preset]); cfg['preset'] = preset
    cfg['run_label'] = preset + '_run3'
    cfg['max_output_tokens'] = MAX_OUT
    key = os.environ.get(ENV_OF[preset])
    if not key:
        print(f'[{preset}] MISSING ENV', flush=True); return
    _, rows = load_benchmark(ROOT, 'crmarena')
    plan = make_plan(rows, 3, int(exp['run_order_seed']), cfg['run_label'])
    plan = [r for r in plan if r['repeat_id'] == REP]
    runroot = ROOT / 'results' / cfg['run_label']
    for sub in ('requests', 'raw', 'normalized'):
        p = runroot / sub
        if not p.exists():
            p.mkdir(parents=True)
    write_json_atomic(runroot / 'FROZEN_MODEL_CONFIG.json', safe_model_config(cfg))
    write_json_atomic(runroot / 'DISCLOSED_CHANGES.json', {
        'note': 'Round-3 (third independent repeat). 300s SLA hard budget: timeout -> fail, no retry. max_output=120000.',
        'changed_fields': {'max_output_tokens': 120000, 'timeout_seconds': 300, 'repeat': 3},
        'date': '2026-10-03'})
    done = 0
    for i, r in enumerate(plan, 1):
        rid = r['run_id']
        norm = runroot / 'normalized' / f'{sha256_text(rid)[:16]}.json'
        if norm.exists():
            done += 1
            continue
        prompt_path = ROOT / r['prompt_path']
        prompt = prompt_path.read_text(encoding='utf-8')
        if sha256_text(prompt) != r['prompt_sha256']:
            raise RuntimeError('Prompt hash mismatch ' + str(prompt_path))
        reqfile = runroot / 'requests' / f'{sha256_text(rid)[:16]}.json'
        if reqfile.exists():
            body = read_json(reqfile)['body']
        else:
            call_id = str(uuid.uuid4())
            body = build_request(cfg, exp['system_instruction'], prompt, call_id)
            write_json_atomic(reqfile, {'run_id': rid, 'call_id': call_id,
                'model_config': safe_model_config(cfg), 'prompt_sha256': r['prompt_sha256'], 'body': body})
        try:
            res = call(cfg, key, body, timeout=TIMEOUT)
        except requests.exceptions.Timeout:
            res = {'raw': {'error': 'timeout'}, 'text': '', 'usage': {},
                   'finish_reason': 'timeout', 'latency_ms': TIMEOUT * 1000,
                   'response_model': '', 'request_id': ''}
        except ProviderError as e:
            msg = str(e); m = re.search(r'"status"\s*:\s*(\d+)', msg)
            status = int(m.group(1)) if m else None
            if status in retry_statuses:
                time.sleep(2); 
            res = {'raw': {'error': msg[:500]}, 'text': '', 'usage': {},
                   'finish_reason': 'provider_error', 'latency_ms': 0,
                   'response_model': '', 'request_id': ''}
        rawfile = runroot / 'raw' / f'{sha256_text(rid)[:16]}.json'
        write_json_atomic(rawfile, res['raw'])
        rec = {**r, 'requested_model': cfg['model'], 'response_model': res['response_model'],
               'finish_reason': res['finish_reason'], 'latency_ms': res['latency_ms'],
               'request_id': res['request_id'], 'usage': res['usage'], 'text': res['text'],
               'attempts': 1, 'call_id': rid, 'prompt_chars': len(prompt)}
        write_json_atomic(norm, rec)
        done += 1
        u = res['usage'] or {}
        print(f'[{preset}][{done}/{len(plan)}] {r["condition"][:2]}/{r["task_id"].split("_")[1]} r3 '
              f'finish={res["finish_reason"]} lat={res["latency_ms"]//1000}s reason={u.get("reasoning_tokens")}', flush=True)
    print(f'DONE {preset}: {done}/{len(plan)}', flush=True)


if __name__ == '__main__':
    threads = [threading.Thread(target=run_model, args=(p,), name=p) for p in MODELS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print('ALL R3 DONE')
