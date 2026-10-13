import hashlib,random
CONDITIONS=['B0_RUNTIME_HEAVY','B1_TASK_LOCALIZED','B2_DECISION_SUFFICIENT']

def make_plan(rows,repeats,seed,model_label):
    by={}
    for r in rows: by.setdefault(r['task_id'],{})[r['condition']]=r
    tasks=sorted(by)
    out=[]
    for rep in range(1,repeats+1):
        for ti,task in enumerate(tasks):
            missing=[c for c in CONDITIONS if c not in by[task]]
            if missing: raise RuntimeError(f'{task} missing {missing}')
            rot=(ti+rep-1)%3
            order=CONDITIONS[rot:]+CONDITIONS[:rot]
            for c in order:
                r=dict(by[task][c]); r.update({'repeat_id':rep,'model_label':model_label,
                  'run_id':f"{model_label}__{r['benchmark']}__{task}__{c}__r{rep}"})
                out.append(r)
    # shuffle task blocks minimally? preserve Latin condition rotations; deterministic task ordering per repeat
    return out
