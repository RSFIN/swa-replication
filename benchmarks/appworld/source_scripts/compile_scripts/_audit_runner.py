from __future__ import annotations
from _shared import *
import ast
import math
from appworld import AppWorld
from appworld.common.datetime import VanillaDateTime as DateTime
from swa_appworld.context_audit import oracle_from_context, semantic_boundary, evidence_ids_from_context
from swa_appworld.row_table import decode_feed
from swa_appworld.render import parse_prompt, render_context
from swa_appworld.bundle import REQUIRED_GATES

GATES = REQUIRED_GATES


def native_equal(family, actual, native):
    if family == '50e1ac9':
        normalize = lambda text: sorted(part.strip().lower() for part in str(text).split(','))
        return normalize(actual) == normalize(native)
    return actual == native


def no_hidden_access():
    files = list((ROOT / 'swa_appworld/adapters').glob('*.py'))
    files += [ROOT / 'swa_appworld/common.py', ROOT / 'swa_appworld/render.py',
              ROOT / 'swa_appworld/row_table.py', ROOT / 'scripts/_compile_worker.py']
    prohibited = {'ground_truth', 'compiled_solution_code', 'solution_code', 'evaluation_code', 'private_data', 'public_data', 'oracle_answer'}
    for file in files:
        for node in ast.walk(ast.parse(file.read_text(encoding='utf-8'))):
            if isinstance(node, ast.Attribute) and node.attr in prohibited: return False
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'getattr':
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) and node.args[1].value in prohibited: return False
    return True


def main():
    cfg = load_cfg(); comp = ROOT / 'LOCAL_ONLY_OUTPUT/compiled'
    ready = comp / 'READY.json'; ready.unlink(missing_ok=True)
    with (comp / 'manifest.csv').open(encoding='utf-8') as file:
        manifest = list(csv.DictReader(file))
    expected = {(tid, c) for tid in cfg['formal_instances'] for c in cfg['conditions']}
    if len(manifest) != len(expected) or {(r['task_id'], r['condition']) for r in manifest} != expected:
        raise SystemExit('Manifest does not match the frozen sample')
    measured = json.loads((comp / 'latency_measurement.json').read_text())
    file_hashes = json.loads((comp / 'source_hashes.json').read_text())
    if not all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in file_hashes.items()):
        raise SystemExit('Compiler source/config changed after materialization')
    rows = []; details = {}; sealed = {}; isolation = no_hidden_access()
    for tid in cfg['formal_instances']:
        family = family_id(tid); adapter = REGISTRY[family]; instruction = None
        contexts = {}; intact = True; prompt_roundtrip = True; latency_valid = True; lengths = {}
        for condition in cfg['conditions']:
            item = next(r for r in manifest if r['task_id'] == tid and r['condition'] == condition)
            text = (comp / 'contexts' / f'{tid}_{condition}.json').read_text(encoding='utf-8')
            prompt = (comp / 'prompts' / f'{tid}_{condition}.txt').read_text(encoding='utf-8')
            intact &= sha_text(text) == item['context_sha256'] and sha_text(prompt) == item['prompt_sha256']
            obj = json.loads(text); parsed = parse_prompt(prompt)
            prompt_roundtrip &= parsed['context'] == obj and parsed['task_id'] == tid and parsed['condition'] == condition
            prompt_roundtrip &= prompt == render(tid, parsed['instruction'], condition, obj)
            if instruction is not None: prompt_roundtrip &= instruction == parsed['instruction']
            instruction = parsed['instruction']; contexts[condition] = parsed['context']
            lengths[condition] = len(SYSTEM) + len(prompt)
            intact &= lengths[condition] == int(item['rendered_prompt_chars']) and len(render_context(obj)) == int(item['context_chars'])
            elapsed = float(item['compiler_ms'])
            latency_valid &= math.isfinite(elapsed) and elapsed > 0 and int(item['worker_pid']) != int(item['parent_pid'])
            latency_valid &= item['clock_source'] == 'parent_perf_counter_ns' and int(item['parent_pid']) == measured['parent_pid']
        # Only the actual prompt's instruction and parsed context enter these calls.
        answers = {c: oracle_from_context(family, c, instruction, contexts[c]) for c in cfg['conditions']}
        boundary = semantic_boundary(family, instruction, contexts['B0'], contexts['B1'], contexts['B2'])
        evidence = evidence_ids_from_context(family, instruction, contexts['B0'])
        deterministic = True; lossless = True; native_scores = {}; native = None
        for repeat in range(2):
            with AppWorld(task_id=tid, experiment_name=f'swa_v3_2_audit_{repeat}', ground_truth_mode='full', raise_on_failure=False) as world:
                rt = CompilerRuntime(tid, world.task.instruction, world.apis, DateTime.now())
                source, b0, b1, b2 = adapter.build_all(rt)
                metadata = {'current_datetime': rt.now.isoformat(), 'user_email': world.apis.supervisor.show_profile()['email']}
                for c, obj in zip(['B0', 'B1', 'B2'], [b0, b1, b2]):
                    deterministic &= sha256_obj({**obj, 'task_metadata': metadata}) == sha256_obj(contexts[c])
                if family == '383cbac':
                    lossless &= decode_feed(contexts['B0']['primitive_social_feed_table']) == source['social_feed']
                    lossless &= contexts['B0']['primitive_contacts'] == source['contacts']
                # Hidden answer/evaluator access is restricted to this audit layer.
                native = world.task.ground_truth.answer
                if repeat == 0:
                    for c in cfg['conditions']:
                        world.apis.supervisor.complete_task(answer=answers[c])
                        tracker = world.evaluate(suppress_errors=False)
                        native_scores[c] = bool(tracker.success)
        row = {'task_id': tid, 'scenario_id': family,
               'provenance_pass': boundary['checks']['b2_complete_primitive_evidence_in_prescribed_order'],
               **{f'sufficiency_{c.lower()}_pass': native_equal(family, answers[c], native) for c in cfg['conditions']},
               **{f'native_evaluator_{c.lower()}_pass': native_scores[c] for c in cfg['conditions']},
               'treatment_boundary_pass': boundary['pass'], 'no_hidden_solution_pass': isolation,
               'determinism_pass': deterministic, 'b0_bounded_pass': lengths['B0'] <= cfg['max_b0_chars'],
               'b0_lossless_pass': lossless, 'rendered_prompt_roundtrip_pass': prompt_roundtrip,
               'artifact_hashes_pass': intact, 'latency_measurement_pass': latency_valid,
               'b0_rendered_prompt_chars': lengths['B0'], 'b0_chars': len(render_context(contexts['B0']))}
        row['sufficiency_pass'] = all(row[f'sufficiency_{c.lower()}_pass'] and native_scores[c] for c in cfg['conditions'])
        rows.append(row)
        details[tid] = {'context_oracle_answers': answers, 'native_answer': native, 'native_evaluator_pass': native_scores,
                        'semantic_boundary': boundary, 'evidence_ids': evidence}
        sealed[tid] = {'native_answer': native, 'oracle_answer': answers['B2'], 'context_oracle_answers': answers, 'evidence_ids': evidence}
        print(tid, 'PASS' if all(row[g] for g in GATES) else 'FAIL', 'B0 rendered chars', lengths['B0'], flush=True)
    with (comp / 'audit.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (comp / 'sealed/audit_details.json').write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding='utf-8')
    (comp / 'sealed/oracle.json').write_text(json.dumps(sealed, ensure_ascii=False, indent=2), encoding='utf-8')
    failed = [row for row in rows if not all(row[g] for g in GATES)]
    if failed:
        print(json.dumps(failed, indent=2)); raise SystemExit(f'FAIL: {len(failed)} task(s) failed formal audit')
    ready_data = {'ready': True, 'version': '3.2', 'tasks': len(rows), 'contexts': len(manifest), 'all_audits_pass': True,
                  'context_oracle_native_checks': len(rows) * 3, 'semantic_family_audits': len(rows),
                  'max_rendered_b0_prompt_chars': max(row['b0_rendered_prompt_chars'] for row in rows),
                  'max_b0_chars_gate': cfg['max_b0_chars'], 'gate_scope': 'SYSTEM_PROMPT plus rendered user prompt',
                  'participant_interning': False, 'lexical_prefix_encoding': False, 'plain_tsv': True, 'latency_clock': measured['clock'], 'latency_scope': 'cold_end_to_end_subprocess_wall_clock',
                  'audit_sha256': hashlib.sha256((comp / 'audit.csv').read_bytes()).hexdigest(),
                  'manifest_sha256': hashlib.sha256((comp / 'manifest.csv').read_bytes()).hexdigest()}
    ready.write_text(json.dumps(ready_data, indent=2), encoding='utf-8')
    print('PASS: all strengthened formal AppWorld audits', len(rows), 'tasks')
