#!/usr/bin/env python3
"""Robust single-model formal runner (round 2). Runs ONE model's 60 CRMArena calls strictly
sequentially, with a large output budget, a long timeout, and retry on BOTH HTTP errors and
network-layer failures (ReadTimeout/ConnectionError/ChunkedEncodingError). Resumable: skips
any call whose normalized record already exists.

Usage: python scripts/run_formal_robust.py <preset> [--max-out 120000] [--timeout 3600]
"""
from pathlib import Path
import sys, os, json, uuid, time, re, argparse
import requests
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.providers import build_request, call, ProviderError
from src.benchmarks import load_benchmark
from src.plan import make_plan
from src.util import read_json, write_json_atomic, safe_model_config, sha256_text

p = argparse.ArgumentParser()
p.add_argument('preset')
p.add_argument('--max-out', type=int, default=120000)
p.add_argument('--timeout', type=int, default=3600)
p.add_argument('--attempts', type=int, default=6)
a = p.parse_args()

exp = read_json(ROOT / 'config/experiment.json')
presets = read_json(ROOT / 'config/model_presets.json')
if a.preset not in presets:
    raise SystemExit('Unknown preset: ' + a.preset)
ENV_OF = {
    'deepseek_v4_pro_0813': 'DEEPSEEK_API_KEY',
    'doubao_seed_2_1_lite_260915': 'ARK_API_KEY',
    'qwen3_8_max_0902': 'DASHSCOPE_API_KEY',
}
cfg = dict(presets[a.preset])
cfg['preset'] = a.preset
cfg['run_label'] = a.preset + '_run1'
cfg['max_output_tokens'] = a.max_out
key = os.environ.get(ENV_OF[a.preset])
if not key:
    raise SystemExit('Missing env ' + ENV_OF[a.preset])

_, rows = load_benchmark(ROOT, 'crmarena')
plan = make_plan(rows, int(exp['repeats']), int(exp['run_order_seed']), cfg['run_label'])
runroot = ROOT / 'results' / cfg['run_label']
for _sub in ('requests', 'raw', 'normalized'):
    _p = runroot / _sub
    if not _p.exists():
        _p.mkdir(parents=True)
write_json_atomic(runroot / 'FROZEN_MODEL_CONFIG.json', safe_model_config(cfg))
write_json_atomic(runroot / 'FROZEN_EXPERIMENT_CONFIG.json', exp)
write_json_atomic(runroot / 'DISCLOSED_CHANGES.json', {
    'note': 'SLA-budget design: max_output_tokens raised to %d (16384 truncated reasoning models on B0); per-call timeout %ds acts as the SLA budget -- a call exceeding it is recorded as finish_reason=timeout with no retry (timeout is a legitimate outcome, not a retryable error).' % (a.max_out, a.timeout),
    'changed_fields': {'max_output_tokens': {'from': 16384, 'to': a.max_out}, 'timeout_seconds': {'from': 1800, 'to': a.timeout}, 'timeout_semantics': 'SLA hard budget; timeout -> fail, no retry'},
    'date': '2026-10-02',
})

retry_statuses = set(exp['retry']['retry_statuses'])
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
        req = read_json(reqfile); call_id = req['call_id']; body = req['body']
    else:
        call_id = str(uuid.uuid4())
        body = build_request(cfg, exp['system_instruction'], prompt, call_id)
        write_json_atomic(reqfile, {'run_id': rid, 'call_id': call_id,
            'model_config': safe_model_config(cfg), 'prompt_sha256': r['prompt_sha256'], 'body': body})
    res = None
    for attempt in range(1, a.attempts + 1):
        try:
            res = call(cfg, key, body, timeout=a.timeout)
            break
        except requests.exceptions.Timeout:
            res = {'raw': {'error': 'timeout'}, 'text': '', 'usage': {},
                   'finish_reason': 'timeout', 'latency_ms': a.timeout * 1000,
                   'response_model': '', 'request_id': ''}
            print(f'[{a.preset}] {rid} SLA-timeout ({a.timeout}s) -> fail, no retry', flush=True)
            break
        except ProviderError as e:
            msg = str(e); m = re.search(r'"status"\s*:\s*(\d+)', msg)
            status = int(m.group(1)) if m else None
            if status not in retry_statuses or attempt == a.attempts:
                raise
            delay = float(exp['retry']['base_delay_seconds']) * (2 ** (attempt - 1))
            print(f'[{a.preset}] {rid} HTTP {status} retry {attempt}/{a.attempts} sleep {delay:.0f}s', flush=True)
            time.sleep(delay)
        except Exception as e:
            if attempt == a.attempts:
                raise
            delay = min(120, 20 * attempt)
            print(f'[{a.preset}] {rid} network {type(e).__name__} retry {attempt}/{a.attempts} sleep {delay}s', flush=True)
            time.sleep(delay)
    rawfile = runroot / 'raw' / f'{sha256_text(rid)[:16]}.json'
    write_json_atomic(rawfile, res['raw'])
    rec = {**r, 'requested_model': cfg['model'], 'response_model': res['response_model'],
           'finish_reason': res['finish_reason'], 'latency_ms': res['latency_ms'],
           'request_id': res['request_id'], 'usage': res['usage'], 'text': res['text'],
           'attempts': attempt, 'call_id': call_id, 'prompt_chars': len(prompt)}
    write_json_atomic(norm, rec)
    done += 1
    u = res['usage'] or {}
    print(f'[{a.preset}][{done}/{len(plan)}] {r["condition"][:2]}/{r["task_id"].split("_")[1]} r{r["repeat_id"]} '
          f'finish={res["finish_reason"]} in={u.get("input_tokens")} out={u.get("output_tokens")} '
          f'reason={u.get("reasoning_tokens")} ms={res["latency_ms"]}', flush=True)
print(f'DONE {a.preset}: {done}/{len(plan)} records', flush=True)
