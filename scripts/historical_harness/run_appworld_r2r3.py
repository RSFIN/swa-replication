#!/usr/bin/env python3
"""AppWorld round-2/3 (second & third independent repeats) runner. Reuses round-1, only runs
repeat_id in {2,3} (180 calls = 3 models x 10 tasks x 3 conditions x 2 repeats), with the
300s SLA hard budget. Writes to separate results/<preset>_r2/ and results/<preset>_r3/ dirs."""
from pathlib import Path
import sys, os, json, uuid, time, re, threading, csv, hashlib
import requests
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.providers import build_request, call, ProviderError
from src.util import read_json, write_json_atomic

BUNDLE = Path('${APPWORLD_BUNDLE_DIR}')
system = (BUNDLE / 'SYSTEM_PROMPT.txt').read_text(encoding='utf-8')
oracle = read_json(BUNDLE / 'SEALED/oracle.json')
model_inputs = read_json(BUNDLE / 'MODEL_INPUTS.json')
presets = read_json(ROOT / 'config/model_presets.json')

MODELS = ['deepseek_v4_pro_0813', 'doubao_seed_2_1_lite_260915', 'qwen3_8_max_0902']
ENV_OF = {
    'deepseek_v4_pro_0813': 'DEEPSEEK_API_KEY',
    'doubao_seed_2_1_lite_260915': 'ARK_API_KEY',
    'qwen3_8_max_0902': 'DASHSCOPE_API_KEY',
}
MAX_OUT = 120000
TIMEOUT = 300
REPS = [2, 3]
RESULTS = BUNDLE / 'results'


def sha256_text(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def parse_final_answer(text):
    m = re.search(r'FINAL_ANSWER\s*:\s*(.*?)\s*$', text, re.M | re.I)
    if m:
        return m.group(1).strip()
    lines = [l for l in text.strip().splitlines() if l.strip()]
    return lines[-1].strip() if lines else ''


def judge(ans, gold):
    if ans is None or ans == '':
        return False
    clean = ans.strip().replace('$', '').replace('USD', '').replace('usd', '').replace(',', '')
    try:
        a = float(clean); g = float(str(gold).replace(',', ''))
        return abs(a - g) < 0.01
    except Exception:
        pass
    if isinstance(gold, str) and ',' in gold:
        ga = sorted(x.strip().lower() for x in ans.split(',') if x.strip())
        gg = sorted(x.strip().lower() for x in gold.split(',') if x.strip())
        return ga == gg
    return ans.strip().lower() == str(gold).strip().lower()


plan = [(p['task_id'], p['condition'], BUNDLE / p['path']) for p in model_inputs['user_prompts']]


def run_model(preset):
    cfg = dict(presets[preset]); cfg['preset'] = preset
    cfg['max_output_tokens'] = MAX_OUT
    key = os.environ.get(ENV_OF[preset])
    if not key:
        print(f'[{preset}] MISSING ENV', flush=True); return
    for rep in REPS:
        cfg['run_label'] = f'{preset}_r{rep}'
        runroot = RESULTS / f'{preset}_r{rep}'
        for sub in ('requests', 'raw', 'normalized'):
            p = runroot / sub
            if not p.exists():
                p.mkdir(parents=True)
        write_json_atomic(runroot / 'DISCLOSED_CHANGES.json', {
            'note': f'AppWorld repeat {rep}. 300s SLA hard budget, timeout -> fail no retry. max_output=120000.',
            'changed_fields': {'max_output_tokens': 120000, 'timeout_seconds': 300, 'repeat': rep},
            'date': '2026-10-03'})
        done = 0
        for (task_id, cond, ppath) in plan:
            rid = f'{preset}__appworld__{task_id}__{cond}__r{rep}'
            norm = runroot / 'normalized' / f'{sha256_text(rid)[:16]}.json'
            if norm.exists():
                done += 1
                continue
            prompt = ppath.read_text(encoding='utf-8')
            call_id = str(uuid.uuid4())
            body = build_request(cfg, system, prompt, call_id)
            try:
                res = call(cfg, key, body, timeout=TIMEOUT)
            except requests.exceptions.Timeout:
                res = {'raw': {'error': 'timeout'}, 'text': '', 'usage': {},
                       'finish_reason': 'timeout', 'latency_ms': TIMEOUT * 1000,
                       'response_model': '', 'request_id': ''}
            except ProviderError as e:
                res = {'raw': {'error': str(e)[:500]}, 'text': '', 'usage': {},
                       'finish_reason': 'provider_error', 'latency_ms': 0,
                       'response_model': '', 'request_id': ''}
            ans = parse_final_answer(res['text'])
            gold = oracle[task_id]['oracle_answer']
            correct = judge(ans, gold)
            u = res.get('usage') or {}
            rec = {'run_id': rid, 'model_label': preset, 'benchmark': 'appworld', 'task_id': task_id,
                   'scenario_id': task_id.split('_')[0], 'condition': cond, 'repeat_id': rep,
                   'finish_reason': res['finish_reason'], 'latency_ms': res['latency_ms'],
                   'input_tokens': u.get('input_tokens'), 'output_tokens': u.get('output_tokens'),
                   'reasoning_tokens': u.get('reasoning_tokens'), 'prompt_chars': len(prompt),
                   'predicted': ans, 'gold': gold, 'correct': int(correct), 'text': res['text']}
            write_json_atomic(norm, rec)
            write_json_atomic(runroot / 'raw' / f'{sha256_text(rid)[:16]}.json', res['raw'])
            done += 1
            print(f'[{preset}_r{rep}][{done}/{len(plan)}] {task_id} {cond} '
                  f'finish={res["finish_reason"]} lat={res["latency_ms"]//1000}s correct={correct}', flush=True)
        print(f'DONE {preset}_r{rep}: {done}/{len(plan)}', flush=True)
    print(f'DONE {preset} (r2+r3)', flush=True)


if __name__ == '__main__':
    threads = [threading.Thread(target=run_model, args=(p,), name=p) for p in MODELS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print('ALL APPWORLD R2R3 DONE')
