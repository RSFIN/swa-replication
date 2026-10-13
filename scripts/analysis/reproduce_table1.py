from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parents[2]
d=pd.read_csv(ROOT/'results/run_level/SWA_900_paper_analysis_runs.csv')
models=['DeepSeek','Doubao','Qwen','GPT','Claude']
rows=[]
for bench in ['CRMArena','AppWorld']:
    for model in models:
        vals=[]
        for scb in ['B0','B1','B2']:
            x=d[(d.benchmark==bench)&(d.model==model)&(d.scb==scb)&(d.completed_within_300s==1)]
            vals.append(np.nan if len(x)==0 else 100*x.final_answer_correct.mean())
        rows.append([bench,model,*vals,(vals[2]-vals[0] if pd.notna(vals[0]) else np.nan)])
    vals=[]
    for scb in ['B0','B1','B2']:
        x=d[(d.benchmark==bench)&(d.scb==scb)&(d.completed_within_300s==1)]
        vals.append(100*x.final_answer_correct.mean())
    rows.append([bench,'Pooled',*vals,vals[2]-vals[0]])
out=pd.DataFrame(rows,columns=['Setting','Model','B0','B1','B2','Delta'])
print(out.to_string(index=False,float_format=lambda v:f'{v:.1f}'))
