"""Reject stale READY markers and unverified artifacts before packaging."""
from __future__ import annotations
import csv
import hashlib
import json

REQUIRED_GATES = ['provenance_pass', 'sufficiency_b0_pass', 'sufficiency_b1_pass', 'sufficiency_b2_pass',
                  'native_evaluator_b0_pass', 'native_evaluator_b1_pass', 'native_evaluator_b2_pass',
                  'treatment_boundary_pass', 'no_hidden_solution_pass', 'determinism_pass', 'b0_bounded_pass',
                  'b0_lossless_pass', 'rendered_prompt_roundtrip_pass', 'artifact_hashes_pass', 'latency_measurement_pass']


def validate_ready(comp, source_root):
    ready = json.loads((comp / 'READY.json').read_text(encoding='utf-8'))
    cfg = json.loads((source_root / 'config/formal_sample.json').read_text(encoding='utf-8'))
    expected = {(t, c) for t in cfg['formal_instances'] for c in cfg['conditions']}
    if not ready.get('ready') or not ready.get('all_audits_pass'): raise ValueError('Bundle is not READY')
    if ready['tasks'] != len(cfg['formal_instances']) or ready['contexts'] != len(expected): raise ValueError('Wrong READY counts')
    for name in ['manifest', 'audit']:
        if hashlib.sha256((comp / (name + '.csv')).read_bytes()).hexdigest() != ready[name + '_sha256']:
            raise ValueError('Audit/manifest changed after READY')
    with (comp / 'manifest.csv').open(encoding='utf-8') as file:
        rows = list(csv.DictReader(file))
    if len(rows) != len(expected) or {(r['task_id'], r['condition']) for r in rows} != expected:
        raise ValueError('Frozen sample mismatch')
    with (comp / 'audit.csv').open(encoding='utf-8') as file:
        audit = list(csv.DictReader(file))
    if len(audit) != len(cfg['formal_instances']) or {r['task_id'] for r in audit} != set(cfg['formal_instances']):
        raise ValueError('Missing task audits')
    if not all(row.get(gate) == 'True' for row in audit for gate in REQUIRED_GATES): raise ValueError('A required audit failed')
    for row in rows:
        for folder, suffix, key in [('contexts', '.json', 'context_sha256'), ('prompts', '.txt', 'prompt_sha256')]:
            file = comp / folder / (row['task_id'] + '_' + row['condition'] + suffix)
            if hashlib.sha256(file.read_bytes()).hexdigest() != row[key]: raise ValueError('Context/prompt changed after audit')
    hashes = json.loads((comp / 'source_hashes.json').read_text(encoding='utf-8'))
    for name, digest in hashes.items():
        if hashlib.sha256((source_root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Source changed after compilation')
    return ready
