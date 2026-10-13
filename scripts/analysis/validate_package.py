from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
d=pd.read_csv(ROOT/'results/run_level/SWA_900_paper_analysis_runs.csv')
key=['benchmark','model','repeat','task_id','scb']
assert len(d)==900, f'Expected 900 rows, found {len(d)}'
assert len(d[key].drop_duplicates())==900, 'Duplicate planned-run keys found'
assert set(d['benchmark'])=={'CRMArena','AppWorld'}
assert set(d['scb'])=={'B0','B1','B2'}
assert d.groupby(['benchmark','model','scb']).size().eq(30).all(), 'Each benchmark/model/SCB cell must contain 30 planned runs'
print('OK: 900 unique planned runs; every benchmark/model/SCB cell has 30 runs.')
