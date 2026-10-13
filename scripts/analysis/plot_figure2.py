#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import fitz
import base64
import cairosvg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTDIR = ROOT / "reproduced"
OUTDIR.mkdir(exist_ok=True)
df = pd.read_csv(ROOT / "results/paper_metrics/Figure2_metrics.csv")

MODELS = ["DS","DB","QW","GPT","CLD"]
CONDS = ["B0","B1","B2"]
# Colorblind-safe palette (seaborn colorblind): deep blue / amber / teal
COLORS = {"B0":"#0173B2","B1":"#DE8F00","B2":"#029E73"}

plt.rcParams.update({
    "font.family":"DejaVu Sans",
    "font.size":7.2,
    "axes.titlesize":8.2,
    "axes.labelsize":6.9,
    "xtick.labelsize":7.0,
    "ytick.labelsize":6.6,
    "axes.linewidth":0.6,
    "hatch.linewidth":0.55,
})

def fmt_pct(v):
    return str(int(round(v))) if abs(v-round(v)) < 0.05 else f"{v:.1f}"

def panel(metric, bench, name):
    sub = df[df.Benchmark.eq(bench)].copy()
    fig = plt.figure(figsize=(2.28,1.48))
    ax = fig.add_axes([0.18,0.21,0.79,0.70])
    x = np.arange(len(MODELS))*1.06
    width = 0.21

    if metric == "reliability":
        vals_by_c = {
            c:[float(sub[(sub.Model==m)&(sub.SCB==c)].Reliability_pct.iloc[0]) for m in MODELS]
            for c in CONDS
        }
        centers = {c: x+(j-1)*width for j,c in enumerate(CONDS)}
        for j,c in enumerate(CONDS):
            ax.bar(centers[c], vals_by_c[c], width=width,
                   color=COLORS[c], edgecolor="white", linewidth=0.35)

        pad = 0.012
        def x_left(xc): return xc - width/2 + pad
        def x_right(xc): return xc + width/2 - pad

        if bench == "CRMArena":
            # DS: show 60 on B0; one black 100 for the B1/B2 pair above the plot region.
            i = MODELS.index("DS")
            ax.text(x_right(centers["B0"][i]), 61.5, "60",
                    ha="right", va="bottom", fontsize=4.75, color=COLORS["B0"], fontweight="bold")
            ax.text((centers["B1"][i]+centers["B2"][i])/2, 103.0, "100",
                    ha="center", va="bottom", fontsize=4.8, color="black",
                    fontweight="bold", clip_on=False)

            # DB: 43.3 right, 93.3 right, 100 left.
            i = MODELS.index("DB")
            ax.text(x_right(centers["B0"][i]), 44.8, "43.3",
                    ha="right", va="bottom", fontsize=4.75, color=COLORS["B0"], fontweight="bold")
            ax.text(x_right(centers["B1"][i]), 94.8, "93.3",
                    ha="right", va="bottom", fontsize=4.75, color=COLORS["B1"], fontweight="bold")
            ax.text(x_left(centers["B2"][i]), 98.7, "100",
                    ha="left", va="top", fontsize=4.75, color=COLORS["B2"], fontweight="bold")

            # QW: 0 / 16.7 / 96.7
            i = MODELS.index("QW")
            ax.text(x_left(centers["B0"][i]), 1.8, "0",
                    ha="left", va="bottom", fontsize=4.75, color=COLORS["B0"], fontweight="bold")
            ax.text(x_right(centers["B1"][i]), 18.2, "16.7",
                    ha="right", va="bottom", fontsize=4.75, color=COLORS["B1"], fontweight="bold")
            ax.text(x_left(centers["B2"][i]), 97.9, "96.7",
                    ha="left", va="bottom", fontsize=4.75, color=COLORS["B2"], fontweight="bold")

            # GPT: 80 right, 93.3 right, green 100 above the plot region, left-aligned to its bar.
            i = MODELS.index("GPT")
            ax.text(x_right(centers["B0"][i]), 81.5, "80",
                    ha="right", va="bottom", fontsize=4.75, color=COLORS["B0"], fontweight="bold")
            ax.text(x_right(centers["B1"][i]), 94.8, "93.3",
                    ha="right", va="bottom", fontsize=4.75, color=COLORS["B1"], fontweight="bold")
            ax.text(x_left(centers["B2"][i]), 103.0, "100",
                    ha="left", va="bottom", fontsize=4.8, color=COLORS["B2"],
                    fontweight="bold", clip_on=False)

            # CLD: one unified black 100 above the plot region.
            i = MODELS.index("CLD")
            ax.text(np.mean([centers["B0"][i], centers["B1"][i], centers["B2"][i]]), 103.0, "100",
                    ha="center", va="bottom", fontsize=4.8, color="black",
                    fontweight="bold", clip_on=False)

        else:  # AppWorld
            # DS, DB, GPT, CLD: one unified black 100 above the plot region.
            for model in ["DS","DB","GPT","CLD"]:
                i = MODELS.index(model)
                ax.text(np.mean([centers["B0"][i], centers["B1"][i], centers["B2"][i]]), 103.0, "100",
                        ha="center", va="bottom", fontsize=4.8, color="black",
                        fontweight="bold", clip_on=False)

            # QW: 90 on B0, one black 100 for B1/B2 above the plot region.
            i = MODELS.index("QW")
            ax.text(x_right(centers["B0"][i]), 91.5, "90",
                    ha="right", va="bottom", fontsize=4.75, color=COLORS["B0"], fontweight="bold")
            ax.text((centers["B1"][i]+centers["B2"][i])/2, 103.0, "100",
                    ha="center", va="bottom", fontsize=4.8, color="black",
                    fontweight="bold", clip_on=False)

        ax.set_ylim(0,100)
        ax.set_ylabel("Completion within 300 s (%)")
        ax.yaxis.set_major_locator(mticker.MultipleLocator(20))

    elif metric == "tokens":
        # Intentionally preserve the uploaded/base version's Token Usage layout:
        # no staircase logic; labels sit just above their own bars.
        for i,m in enumerate(MODELS):
            xposs = [x[i]+(j-1)*width for j in range(3)]
            for j,c in enumerate(CONDS):
                r = sub[(sub.Model==m)&(sub.SCB==c)].iloc[0]
                inp, out = r.Input_Tokens_Mean, r.Output_Tokens_Mean
                if pd.isna(inp) or pd.isna(out):
                    ax.text(xposs[j]-width/2+0.01,
                            3500 if bench=="CRMArena" else 900,
                            "N/A", ha="left", va="bottom",
                            fontsize=4.9, color=COLORS["B0"], fontweight="bold")
                    continue
                total = inp + out
                # output: hatched lower segment; input: solid upper segment
                ax.bar(xposs[j], out, width=width, color="white",
                       edgecolor=COLORS[c], linewidth=0.90, hatch="//////")
                ax.bar(xposs[j], inp, bottom=out, width=width,
                       color=COLORS[c], edgecolor="white", linewidth=0.30)
                offset = 2600 if bench=="CRMArena" else 650
                ax.text(xposs[j]-width/2+0.01, total+offset,
                        f"{int(round(total)):,}",
                        ha="left", va="bottom", fontsize=4.8,
                        color=COLORS[c], fontweight="bold")

        if bench=="CRMArena":
            ax.set_ylim(0,140000)
            ax.yaxis.set_major_locator(mticker.MultipleLocator(20000))
        else:
            ax.set_ylim(0,40000)
            ax.yaxis.set_major_locator(mticker.MultipleLocator(10000))
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v,pos: f"{int(v/1000)}k" if v>=1000 else f"{int(v)}")
        )
        ax.set_ylabel("Mean tokens /\ncompleted request", fontsize=6.2)

    elif metric == "latency":
        vals_by_c = {
            c:[sub[(sub.Model==m)&(sub.SCB==c)].Request_Latency_Median_s.iloc[0] for m in MODELS]
            for c in CONDS
        }
        centers = {c: x+(j-1)*width for j,c in enumerate(CONDS)}
        for j,c in enumerate(CONDS):
            for i,m in enumerate(MODELS):
                v = vals_by_c[c][i]
                xp = centers[c][i]
                if not pd.isna(v):
                    ax.bar(xp, v, width=width, color=COLORS[c],
                           edgecolor="white", linewidth=0.35)

        # Default placement: close to each bar top.
        # Skip the clusters that receive explicit custom staircase labels below,
        # otherwise the default labels would remain underneath and create overlap.
        special_models = set()
        if bench == "CRMArena":
            special_models = {"CLD"}
        elif bench == "AppWorld":
            special_models = {"GPT", "CLD"}

        for i,m in enumerate(MODELS):
            if m in special_models:
                continue
            for j,c in enumerate(CONDS):
                xp = centers[c][i]
                v = vals_by_c[c][i]
                if pd.isna(v):
                    ax.text(xp-width/2+0.01, 4.5, "N/A",
                            ha="left", va="bottom", fontsize=4.8,
                            color=COLORS["B0"], fontweight="bold")
                else:
                    ax.text(xp-width/2+0.01, v + (5.0 if bench=="CRMArena" else 2.5),
                            f"{v:.1f}", ha="left", va="bottom",
                            fontsize=4.8, color=COLORS[c], fontweight="bold")

        # Targeted overrides only for the clusters explicitly requested by the user.
        # Principle: (1) outside all bars, (2) larger values higher, (3) no overlap.
        if bench == "CRMArena":
            # CLD: use a clear staircase layout like the user-provided example:
            # blue low, orange middle, green high; no overlap.
            i = MODELS.index("CLD")
            special = [
                # Extra widening for CRMArena CLD only.
                ("B0", 22.0, "21.0", COLORS["B0"]),
                ("B1", 40.5, "25.0", COLORS["B1"]),
                ("B2", 59.0, "21.0", COLORS["B2"]),
            ]
            for c, yy, txt, col in special:
                xp = centers[c][i]
                ax.text(xp-width/2+0.01, yy, txt,
                        ha="left", va="bottom", fontsize=4.8, color=col, fontweight="bold",
                        bbox=dict(facecolor="white", edgecolor="none", pad=0.12))

        if bench == "AppWorld":
            # GPT: staircase layout matching the provided example.
            i = MODELS.index("GPT")
            special = [
                ("B0", 34.2, "31.4", COLORS["B0"]),
                ("B1", 43.6, "37.5", COLORS["B1"]),
                ("B2", 53.0, "29.0", COLORS["B2"]),
            ]
            for c, yy, txt, col in special:
                xp = centers[c][i]
                ax.text(xp-width/2+0.01, yy, txt,
                        ha="left", va="bottom", fontsize=4.8, color=col, fontweight="bold",
                        bbox=dict(facecolor="white", edgecolor="none", pad=0.12))

            # CLD: staircase layout matching the provided example.
            i = MODELS.index("CLD")
            special = [
                # Further widened staircase for AppWorld CLD.
                ("B0", 20.5, "19.9", COLORS["B0"]),
                ("B1", 30.5, "16.0", COLORS["B1"]),
                ("B2", 40.5, "11.8", COLORS["B2"]),
            ]
            for c, yy, txt, col in special:
                xp = centers[c][i]
                ax.text(xp-width/2+0.01, yy, txt,
                        ha="left", va="bottom", fontsize=4.8, color=col, fontweight="bold",
                        bbox=dict(facecolor="white", edgecolor="none", pad=0.12))

        if bench=="CRMArena":
            ax.set_ylim(0,300)
            ax.yaxis.set_major_locator(mticker.MultipleLocator(50))
        else:
            ax.set_ylim(0,150)
            ax.yaxis.set_major_locator(mticker.MultipleLocator(25))
        ax.set_ylabel("Median request latency (s)")

    ax.set_xticks(x)
    ax.set_xticklabels(MODELS)
    ax.set_title(bench, fontweight="bold", pad=18,
                 bbox=dict(facecolor="white", edgecolor="#B8B8B8", linewidth=0.55,
                           boxstyle="round,pad=2.0,rounding_size=1.2"))
    ax.set_facecolor("#FAFAFA")
    ax.grid(axis="y", color="#DDDDDD", alpha=0.85, linewidth=0.45, linestyle="--")
    ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_color("#A0A0A0")
        sp.set_linewidth(0.55)

    pdf = OUTDIR / f"{name}.pdf"
    svg = OUTDIR / f"{name}.svg"
    png = OUTDIR / f"{name}.png"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.025)
    fig.savefig(svg, bbox_inches="tight", pad_inches=0.025)
    fig.savefig(png, dpi=600, bbox_inches="tight", pad_inches=0.025)
    plt.close(fig)
    return pdf,svg,png

panels={}
for metric in ["reliability","tokens","latency"]:
    for bench in ["CRMArena","AppWorld"]:
        panels[(metric,bench)] = panel(metric,bench,f"panel_{metric}_{bench.lower()}")

# Assemble paper-width vector PDF
OUT_PDF = OUTDIR/"Figure2_reproduced.pdf"
OUT_SVG = OUTDIR/"Figure2_reproduced.svg"
OUT_PNG = OUTDIR/"Figure2_reproduced_600dpi.png"

W,H = 7.16*72,3.15*72
doc=fitz.open()
page=doc.new_page(width=W,height=H)
headings=["(a) Reliability","(b) Token Usage","(c) Request Latency"]

def _icon_clock(cx, cy, r=3.4, color=(0.28,0.28,0.28)):
    page.draw_circle(fitz.Point(cx,cy), r, color=color, width=0.7)
    page.draw_line(fitz.Point(cx,cy), fitz.Point(cx,cy-r*0.62), color=color, width=0.6)
    page.draw_line(fitz.Point(cx,cy), fitz.Point(cx+r*0.55,cy), color=color, width=0.6)

def _icon_bars(x0, cy, color=(0.28,0.28,0.28)):
    for k,(w,hh) in enumerate([(1.3,3.8),(1.3,5.4),(1.3,3.0)]):
        page.draw_rect(fitz.Rect(x0+k*2.0, cy-hh, x0+k*2.0+w, cy), color=color, fill=color, width=0)

def _icon_bolt(x0, cy, color=(0.28,0.28,0.28)):
    pts=[fitz.Point(x0,cy-5.2), fitz.Point(x0+2.8,cy-5.2), fitz.Point(x0+1.5,cy-1.0),
         fitz.Point(x0+4.4,cy-1.0), fitz.Point(x0-1.3,cy+5.2), fitz.Point(x0,cy+0.6),
         fitz.Point(x0-2.8,cy+0.6)]
    page.draw_polyline(pts, color=color, width=0.7)

for i,h in enumerate(headings):
    x0=i*W/3
    cxc = x0 + W/6
    tw = fitz.get_text_length(h, fontname="helv", fontsize=8.8)
    page.insert_text(fitz.Point(cxc - tw/2, 13), h, fontsize=8.8, fontname="helv", color=(0,0,0))
    page.draw_line(fitz.Point(x0+6, 17.4), fitz.Point(x0+W/3-6, 17.4),
                   color=(0.82,0.82,0.82), width=0.5)
    ix = cxc + tw/2 + 4.5
    if i==0:
        _icon_clock(ix, 10)
    elif i==1:
        _icon_bars(ix-3.5, 10)
    else:
        _icon_bolt(ix-3.5, 10)

margin_x=3
top=18
footer_h=24
usable_h=H-top-footer_h
cell_w=(W-2*margin_x)/3
cell_h=usable_h/2
order=[
    ("reliability","CRMArena"),("tokens","CRMArena"),("latency","CRMArena"),
    ("reliability","AppWorld"),("tokens","AppWorld"),("latency","AppWorld")
]
for idx,key in enumerate(order):
    r,c=divmod(idx,3)
    rect=fitz.Rect(margin_x+c*cell_w,top+r*cell_h,
                   margin_x+(c+1)*cell_w,top+(r+1)*cell_h)
    src=fitz.open(panels[key][0])
    page.show_pdf_page(rect,src,0,keep_proportion=True)
    src.close()

# Footer legend with soft background band, matching the base figure.
y=H-12
page.draw_rect(fitz.Rect(6, y-7.5, W-6, y+7.5),
               color=(0.93,0.93,0.93), fill=(0.93,0.93,0.93), width=0.5)
x=28
rgb={"B0":(0.0039,0.4510,0.6980),
     "B1":(0.8706,0.5608,0.0),
     "B2":(0.0078,0.6196,0.4510)}
def box(x,y,color,hatched=False):
    rect=fitz.Rect(x,y-5,x+7,y+2)
    page.draw_rect(rect,color=color,fill=color if not hatched else (1,1,1),width=0.7)
    if hatched:
        for x1,y1,x2,y2 in [
            (x+0.8,y+1.4,x+2.2,y-4.3),
            (x+2.6,y+1.4,x+4.0,y-4.3),
            (x+4.4,y+1.4,x+5.8,y-4.3),
            (x+6.0,y+0.4,x+6.6,y-2.2),
        ]:
            page.draw_line(fitz.Point(x1,y1),fitz.Point(x2,y2),color=color,width=0.55)
for lab in CONDS:
    box(x,y,rgb[lab],False)
    page.insert_text(fitz.Point(x+9,y+1),lab,fontsize=6.0,fontname="helv")
    x+=31
page.insert_text(fitz.Point(x,y+1),"|",fontsize=6.0,fontname="helv"); x+=9
box(x,y,(0.25,0.25,0.25),False)
page.insert_text(fitz.Point(x+9,y+1),"Input (solid)",fontsize=5.8,fontname="helv"); x+=50
box(x,y,(0.25,0.25,0.25),True)
page.insert_text(fitz.Point(x+9,y+1),"Output (hatched)",fontsize=5.8,fontname="helv"); x+=57
page.insert_text(fitz.Point(x,y+1),"|",fontsize=6.0,fontname="helv"); x+=5
footer="DS=DeepSeek V4 Pro; DB=Doubao Seed 2.1 Lite; QW=Qwen3.8 Max; GPT=GPT-5.6 Sol; CLD=Claude Opus 5.5"
page.insert_text(fitz.Point(x,y+1),footer,fontsize=5.2,fontname="helv")
doc.save(OUT_PDF,garbage=4,deflate=True)
doc.close()

# Master SVG with vector panel SVGs embedded
def data_uri(path):
    return "data:image/svg+xml;base64,"+base64.b64encode(Path(path).read_bytes()).decode("ascii")
SW,SH=2148,945
cw=SW/3
header=54
footer=70
ch=(SH-header-footer)/2
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SH}" viewBox="0 0 {SW} {SH}">',
     '<rect width="100%" height="100%" fill="white"/>']
for i,h in enumerate(headings):
    svg.append(f'<text x="{(i+.5)*cw}" y="30" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="27" font-weight="700">{h}</text>')
for idx,key in enumerate(order):
    r,c=divmod(idx,3)
    svg.append(f'<image x="{c*cw+4}" y="{header+r*ch}" width="{cw-8}" height="{ch-4}" preserveAspectRatio="xMidYMid meet" href="{data_uri(panels[key][1])}"/>')
# Simple footer text; PDF is preferred for LaTeX.
svg.append(f'<rect x="14" y="{SH-50}" width="{SW-28}" height="34" fill="#EDEDED" rx="7"/>')
svg.append(f'<text x="{SW/2}" y="{SH-20}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="15">B0 (blue)   B1 (orange)   B2 (green)   |   Input: solid; Output: hatched   |   DS=DeepSeek V4 Pro; DB=Doubao Seed 2.1 Lite; QW=Qwen3.8 Max; GPT=GPT-5.6 Sol; CLD=Claude Opus 5.5</text>')
svg.append('</svg>')
OUT_SVG.write_text("\n".join(svg),encoding="utf-8")
cairosvg.svg2png(url=str(OUT_SVG),write_to=str(OUT_PNG),output_width=4296,output_height=1890)

print(OUT_PDF)
print(OUT_SVG)
print(OUT_PNG)
