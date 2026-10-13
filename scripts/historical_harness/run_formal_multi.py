#!/usr/bin/env python3
"""Concurrent formal runner: runs the three available models in parallel (one thread each),
keeping each model's 60 calls strictly sequential to preserve the Latin-rotation order and
deterministic resume. max_output_tokens is raised to 60000 as a disclosed override (see
DISCLOSED_CHANGES.md) because the shipped 16384 budget truncates reasoning models on B0.
"""
from pathlib import Path
import sys, os, json, uuid, time, re, threading
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
MAX_OUT = 60000

DISCLOSURE = {
    "note": "Shipped max_output_tokens=16384 truncates reasoning models on B0 (reasoning consumes the whole budget, FINAL_ANSWER empty). Raised to 60000 for all three models. qwen already exceeded 16384 on its own; deepseek needs ~36k, doubao ~18k output tokens on B0.",
    "changed_fields": {"max_output_tokens": {"from": 16384, "to": MAX_OUT}},
    "unchanged": ["model id", "reasoning_effort", "thinking mode", "temperature (not overridden)", "endpoint"],
    "date": "2026-10-02",
}

def run_model(preset):
    cfg = dict(presets[preset])
    cfg['preset'] = preset
    cfg['run_label'] = preset + '_run1'
    cfg['max_output_tokens'] = MAX_OUT
    key = os.environ.get(ENV_OF[preset])
    if not key:
        print(f'[{preset}] MISSING ENV {ENV_OF[preset]}', flush=True); return
    _, rows = load_benchmark(ROOT, 'crmarena')
    plan = make_plan(rows, int(exp['repeats']), int(exp['run_order_seed']), cfg['run_label'])
    runroot = ROOT / 'results' / cfg['run_label']
    (runroot / 'requests').mkdir(parents=True, exist_ok=True)
    (runroot / 'raw').mkdir(exist_ok=True)
    (runroot / 'normalized').mkdir(exist_ok=True)
    write_json_atomic(runroot / 'FROZEN_MODEL_CONFIG.json', safe_model_config(cfg))
    write_json_atomic(runroot / 'FROZEN_EXPERIMENT_CONFIG.json', exp)
    write_json_atomic(runroot / 'DISCLOSED_CHANGES.json', DISCLOSURE)
    retry_statuses = set(exp['retry']['retry_statuses'])
    maxa = int(exp['retry']['max_attempts'])
    base = float(exp['retry']['base_delay_seconds'])
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
        for attempt in range(1, maxa + 1):
            try:
                res = call(cfg, key, body, timeout=int(exp['timeout_seconds']))
                break
            except ProviderError as e:
                msg = str(e); m = re.search(r'"status"\s*:\s*(\d+)', msg)
                status = int(m.group(1)) if m else None
                if status not in retry_statuses or attempt == maxa:
                    raise
                time.sleep(base * (2 ** (attempt - 1)))
        rawfile = runroot / 'raw' / f'{sha256_text(rid)[:16]}.json'
        write_json_atomic(rawfile, res['raw'])
        rec = {**r, 'requested_model': cfg['model'], 'response_model': res['response_model'],
               'finish_reason': res['finish_reason'], 'latency_ms': res['latency_ms'],
               'request_id': res['request_id'], 'usage': res['usage'], 'text': res['text'],
               'attempts': attempt, 'call_id': call_id, 'prompt_chars': len(prompt)}
        write_json_atomic(norm, rec)
        done += 1
        u = res['usage'] or {}
        print(f'[{preset}][{done}/{len(plan)}] {r["condition"][:2]}/{r["task_id"].split("_")[1]} r{r["repeat_id"]} '
              f'finish={res["finish_reason"]} in={u.get("input_tokens")} out={u.get("output_tokens")} '
              f'reason={u.get("reasoning_tokens")} ms={res["latency_ms"]}', flush=True)
    print(f'DONE {preset}: {done}/{len(plan)} records', flush=True)

if __name__ == '__main__':
    threads = [threading.Thread(target=run_model, args=(p,), name=p) for p in MODELS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print('ALL MODELS DONE', flush=True)
