"""One task/condition materialization; externally timed by its parent."""
from __future__ import annotations
from _shared import *
import argparse
import os
from appworld import AppWorld
from appworld.common.datetime import VanillaDateTime as DateTime
from swa_appworld.render import render_context


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('task_id'); parser.add_argument('condition'); parser.add_argument('output')
    args = parser.parse_args(); cfg = load_cfg()
    if args.task_id not in cfg['formal_instances'] or args.condition not in cfg['conditions']:
        raise ValueError('Worker input is outside frozen sample')
    output = Path(args.output); key = f'{args.task_id}_{args.condition}'
    adapter = REGISTRY[family_id(args.task_id)]
    with AppWorld(task_id=args.task_id, experiment_name=f'swa_v3_2_compile_{args.condition}',
                  ground_truth_mode='minimal', raise_on_failure=False) as world:
        instruction = world.task.instruction
        rt = CompilerRuntime(args.task_id, instruction, world.apis, DateTime.now())
        source = adapter.collect_source(rt)
        obj = getattr(adapter, 'build_' + args.condition.lower())(rt, source)
        profile = world.apis.supervisor.show_profile()
        obj = {**obj, 'task_metadata': {'current_datetime': rt.now.isoformat(), 'user_email': profile['email']}}
        ctx_text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
        prompt = render(args.task_id, instruction, args.condition, obj)
        (output / 'contexts' / (key + '.json')).write_text(ctx_text, encoding='utf-8')
        (output / 'prompts' / (key + '.txt')).write_text(prompt, encoding='utf-8')
        row = {'benchmark': 'AppWorld', 'task_id': args.task_id, 'scenario_id': family_id(args.task_id),
               'condition': args.condition, 'instruction': instruction,
               'context_chars': len(render_context(obj)), 'context_json_chars': len(ctx_text),
               'prompt_chars': len(prompt), 'rendered_prompt_chars': len(SYSTEM) + len(prompt),
               'context_sha256': sha_text(ctx_text), 'prompt_sha256': sha_text(prompt), 'worker_pid': os.getpid()}
        (output / 'worker_results' / (key + '.json')).write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    print('COMPILED', key)


if __name__ == '__main__': main()
