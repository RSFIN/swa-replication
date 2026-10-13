#!/usr/bin/env python3
"""AppWorld formal runner: 3 models x 10 tasks x 3 SCB conditions = 90 calls.
SLA budget: timeout=300s, a call exceeding it is recorded as finish_reason=timeout with no
retry (timeout is a legitimate outcome). Resumable. Writes evaluated normalized records."""
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
    cfg = dict(presets[preset]); cfg['preset'] = preset; cfg['run_label'] = preset
    cfg['max_output_tokens'] = MAX_OUT
    key = os.environ.get(ENV_OF[preset])
    if not key:
        print(f'[{preset}] MISSING ENV', flush=True); return
    runroot = RESULTS / preset
    for sub in ('requests', 'raw', 'normalized'):
        p = runroot / sub
        if not p.exists():
            p.mkdir(parents=True)
    write_json_atomic(runroot / 'DISCLOSED_CHANGES.json', {
        'note': 'SLA-budget design (same as CRMArena): timeout=300s hard budget, timeout -> fail no retry; max_output=120000 (qwen cap 131072).',
        'changed_fields': {'max_output_tokens': 120000, 'timeout_seconds': 300, 'timeout_semantics': 'SLA hard budget'},
        'date': '2026-10-03'})
    done = 0
    for (task_id, cond, ppath) in plan:
        rid = f'{preset}__appworld__{task_id}__{cond}'
        norm = runroot / 'normalized' / f'{sha256_text(rid)[:16]}.json'
        if norm.exists():
            done += 1
            continue
        prompt = ppath.read_text(encoding='utf-8')
        call_id = str(uuid.uuid4())
        body = build_request(cfg, system, prompt, call_id)
        reqfile = runroot / 'requests' / f'{sha256_text(rid)[:16]}.json'
        if reqfile.exists():
            body = read_json(reqfile)['body']
        else:
            write_json_atomic(reqfile, {'run_id': rid, 'call_id': call_id, 'body': body})
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
               'scenario_id': task_id.split('_')[0], 'condition': cond,
               'finish_reason': res['finish_reason'], 'latency_ms': res['latency_ms'],
               'input_tokens': u.get('input_tokens'), 'output_tokens': u.get('output_tokens'),
               'reasoning_tokens': u.get('reasoning_tokens'), 'prompt_chars': len(prompt),
               'predicted': ans, 'gold': gold, 'correct': int(correct), 'text': res['text']}
        write_json_atomic(norm, rec)
        rawfile = runroot / 'raw' / f'{sha256_text(rid)[:16]}.json'
        write_json_atomic(rawfile, res['raw'])
        done += 1
        print(f'[{preset}][{done}/{len(plan)}] {task_id} {cond} finish={res["finish_reason"]} '
              f'lat={res["latency_ms"]//1000}s reason={u.get("reasoning_tokens")} correct={correct} ans={ans!r}', flush=True)
    print(f'DONE {preset}: {done}/{len(plan)}', flush=True)


if __name__ == '__main__':
    threads = [threading.Thread(target=run_model, args=(p,), name=p) for p in MODELS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # 汇总 CSV
    rows = []
    for preset in MODELS:
        d = RESULTS / preset / 'normalized'
        for f in sorted(d.glob('*.json')):
            r = read_json(f)
            r.pop('text', None)
            rows.append(r)
    if rows:
        out = RESULTS / 'evaluated_combined.csv'
        with open(out, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print('WROTE', out, len(rows), 'rows')
    print('ALL DONE')
