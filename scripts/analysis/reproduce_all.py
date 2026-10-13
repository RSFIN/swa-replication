#!/usr/bin/env python3
from pathlib import Path
import math
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reproduced"
OUT.mkdir(exist_ok=True)

RUNS = ROOT / "results/run_level/SWA_900_paper_analysis_runs.csv"
FROZEN_T1 = ROOT / "results/paper_metrics/Table1_accuracy.csv"
FROZEN_F2 = ROOT / "results/paper_metrics/Figure2_metrics.csv"

models = ["DeepSeek", "Doubao", "Qwen", "GPT", "Claude"]
model_code = {"DeepSeek":"DS", "Doubao":"DB", "Qwen":"QW", "GPT":"GPT", "Claude":"CLD"}
conditions = ["B0", "B1", "B2"]
benchmarks = ["CRMArena", "AppWorld"]

report = []
def log(x=""):
    print(x)
    report.append(str(x))

# ---------------------------
# 1. Validate canonical design
# ---------------------------
d = pd.read_csv(RUNS)
key = ["benchmark","model","repeat","task_id","scb"]
assert len(d) == 900, f"Expected 900 rows, found {len(d)}"
assert len(d[key].drop_duplicates()) == 900, "Duplicate planned-run keys found"
assert set(d.benchmark) == set(benchmarks)
assert set(d.scb) == set(conditions)
assert d.groupby(["benchmark","model","scb"]).size().eq(30).all()
log("PASS: canonical design contains 900 unique planned runs; every benchmark/model/SCB cell has 30 runs.")

# ---------------------------
# 2. Reconstruct Table I
# ---------------------------
rows=[]
for bench in benchmarks:
    for model in models:
        vals=[]
        for scb in conditions:
            x=d[(d.benchmark==bench)&(d.model==model)&(d.scb==scb)&(d.completed_within_300s==1)]
            vals.append(np.nan if len(x)==0 else 100*x.final_answer_correct.mean())
        rows.append([bench,model,*vals,(vals[2]-vals[0] if pd.notna(vals[0]) else np.nan)])
    vals=[]
    for scb in conditions:
        x=d[(d.benchmark==bench)&(d.scb==scb)&(d.completed_within_300s==1)]
        vals.append(100*x.final_answer_correct.mean())
    rows.append([bench,"Pooled",*vals,vals[2]-vals[0]])

t1=pd.DataFrame(rows,columns=["Setting","Model","B0","B1","B2","Delta_B2_minus_B0_pp"])
t1.to_csv(OUT/"Table1_accuracy_reconstructed.csv", index=False)

f1=pd.read_csv(FROZEN_T1)
m=t1.merge(f1,on=["Setting","Model"],suffixes=("_reconstructed","_paper"))
max_t1=0.0
for col in ["B0","B1","B2","Delta_B2_minus_B0_pp"]:
    a=m[f"{col}_reconstructed"]
    b=m[f"{col}_paper"]
    diff=(a-b).abs()
    diff=diff[~(a.isna() & b.isna())]
    if len(diff): max_t1=max(max_t1,float(diff.max()))
if max_t1 < 1e-9:
    log("PASS: Table I reconstructs exactly from the canonical 900-run file.")
else:
    log(f"WARN: Table I maximum absolute difference from paper-frozen values = {max_t1:.6g} percentage points.")

# ---------------------------
# 3. Reconstruct runtime metrics
# ---------------------------
all_cells=pd.MultiIndex.from_product([benchmarks,models,conditions],names=["benchmark","model","scb"]).to_frame(index=False)
rel=(d.groupby(["benchmark","model","scb"]).completed_within_300s.mean()*100).rename("Reliability_pct").reset_index()
completed=d[d.completed_within_300s==1].copy()
agg=completed.groupby(["benchmark","model","scb"]).agg(
    n_completed=("task_id","size"),
    Input_Tokens_Mean=("input_tokens","mean"),
    Output_Tokens_Mean=("output_tokens","mean"),
    Request_Latency_Median_s=("request_latency_s","median")
).reset_index()
f2=all_cells.merge(rel,on=["benchmark","model","scb"],how="left").merge(agg,on=["benchmark","model","scb"],how="left")
f2["n_completed"]=f2["n_completed"].fillna(0).astype(int)
f2["Total_Tokens_Mean"]=f2["Input_Tokens_Mean"]+f2["Output_Tokens_Mean"]
f2["Benchmark"]=f2["benchmark"]
f2["Model"]=f2["model"].map(model_code)
f2["SCB"]=f2["scb"]
f2out=f2[["Benchmark","Model","SCB","Reliability_pct","Input_Tokens_Mean","Output_Tokens_Mean","Request_Latency_Median_s","n_completed","Total_Tokens_Mean"]]
f2out.to_csv(OUT/"Figure2_metrics_reconstructed.csv",index=False)

pf=pd.read_csv(FROZEN_F2)
cmp=f2out.merge(pf,on=["Benchmark","Model","SCB"],suffixes=("_reconstructed","_paper"))
metrics=["Reliability_pct","Input_Tokens_Mean","Output_Tokens_Mean","Request_Latency_Median_s","n_completed","Total_Tokens_Mean"]
for metric in metrics:
    a=cmp[f"{metric}_reconstructed"]
    b=cmp[f"{metric}_paper"]
    cmp[f"{metric}_absdiff"]=(a-b).abs()
cmp.to_csv(OUT/"Figure2_metrics_comparison.csv",index=False)

max_rel=float(cmp["Reliability_pct_absdiff"].fillna(0).max())
max_in=float(cmp["Input_Tokens_Mean_absdiff"].fillna(0).max())
max_out=float(cmp["Output_Tokens_Mean_absdiff"].fillna(0).max())
max_n=float(cmp["n_completed_absdiff"].fillna(0).max())
max_lat=float(cmp["Request_Latency_Median_s_absdiff"].fillna(0).max())

if max(max_rel,max_in,max_out,max_n) < 1e-6:
    log("PASS: Figure 2 reliability, completed-count, and input/output-token summaries reconstruct from the canonical run-level file.")
else:
    log(f"WARN: runtime non-latency summary difference detected (max rel={max_rel:.6g}, input={max_in:.6g}, output={max_out:.6g}, n={max_n:.6g}).")

if max_lat <= 0.35:
    log(f"PASS WITH NOTE: request-latency reconstruction differs from the paper-frozen aggregation by at most {max_lat:.3f} s (known timestamp-aggregation detail).")
else:
    log(f"WARN: request-latency difference exceeds the documented 0.35-s tolerance (max={max_lat:.3f} s).")

# ---------------------------
# 4. Operational-success pooled checkpoints
# ---------------------------
op=(d.groupby(["benchmark","scb"]).operational_success_300.mean()*100).unstack("scb")
op.to_csv(OUT/"Operational_success_pooled.csv")
log("")
log("Pooled operational success (%):")
for bench in benchmarks:
    log(f"  {bench}: B0={op.loc[bench,'B0']:.1f}, B1={op.loc[bench,'B1']:.1f}, B2={op.loc[bench,'B2']:.1f}")

log("")
log("Reproduction outputs written to reproduced/.")
log("For the exact paper Figure 2, run: python scripts/analysis/plot_figure2.py")

(OUT/"reproduction_report.txt").write_text("\n".join(report)+"\n",encoding="utf-8")
