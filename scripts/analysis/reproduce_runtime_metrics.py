from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
d=pd.read_csv(ROOT/'results/run_level/SWA_900_paper_analysis_runs.csv')
completed=d[d.completed_within_300s==1].copy()
rel=(d.groupby(['benchmark','model','scb']).completed_within_300s.mean()*100).rename('Reliability_pct')
met=completed.groupby(['benchmark','model','scb']).agg(
    n_completed=('task_id','size'),
    Input_Tokens_Mean=('input_tokens','mean'),
    Output_Tokens_Mean=('output_tokens','mean'),
    Request_Latency_Median_s=('request_latency_s','median'))
out=met.join(rel).reset_index()
out['Total_Tokens_Mean']=out.Input_Tokens_Mean+out.Output_Tokens_Mean
print(out.to_string(index=False))
print('\nNote: the paper-frozen Figure 2 values are in results/paper_metrics/Figure2_metrics.csv. Small sub-second differences can occur when reconstructing latency from source timestamps versus the paper-frozen aggregation.')
