"""End-to-end analysis. Run from anywhere:  python src/run_analysis.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # make `src` importable

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.data import ROOT, load_orders, did_sample
from src import models, optimise

CAPACITY = 22   # ASSUMPTION: roughly the max daily orders seen in any region
DIST = {3: 9, 4: 15}
LEVERS = [(3, "food"), (4, "fee")]
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

df = load_orders()
res = {}
for region, lever in LEVERS:
    s = did_sample(df, region)
    d, p = models.did_log(s), models.did_poisson(s)
    pre, plc = models.pretrend_test(s), models.placebo_did(s)
    base_q = df[(df.region == region) & (df.post == 0)].qty.mean()
    res[lever] = dict(sample=s, did=d, base_q=base_q)
    lo, hi = d["elasticity_ci"]
    print(f"\n=== Region {region} ({lever} discount) ===")
    print(f"DiD effect on ln(Q): {d['delta']:.3f} (SE {d['delta_se']:.3f}) -> {np.expm1(d['delta']):+.0%} orders")
    print(f"Elasticity {d['elasticity']:.2f}  95% CI [{lo:.2f}, {hi:.2f}] | Poisson {p['elasticity']:.2f}")
    print(f"Pre-trend slope diff {pre['coef']:.3f} (p={pre['p']:.3f}) | placebo DiD {plc['coef']:.3f} (p={plc['p']:.3f})")
    print("IER price (unconstrained):", optimise.ier_price(optimise.effective_mc(lever, DIST[region]), d["elasticity"]))
    base = optimise.profit_curve(lever, base_q, d["elasticity"], DIST[region], [0.0]).profit[0]
    print(f"Baseline contribution ${base:.2f}/day")
    for cap in (None, CAPACITY):
        cur = optimise.profit_curve(lever, base_q, d["elasticity"], DIST[region], [0.05], cap).profit[0]
        print(f" cap={cap}: current 5% -> ${cur:.2f}/day")
        for label, eta in [("point", d["elasticity"]), ("CI low", lo), ("CI high", hi)]:
            b = optimise.best_in_trust_region(lever, base_q, eta, DIST[region], 0.15, cap)
            print(f"   eta={eta:7.2f} ({label:7s}) best discount {b.discount:+.1%}, orders {b.orders:6.1f}, profit ${b.profit:8.2f}/day")

fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
for ax, (r, lever) in zip(axes, LEVERS):
    es = models.event_study(res[lever]["sample"])
    ax.errorbar(es.week, es.coef, yerr=1.96 * es.se, fmt="o", capsize=3)
    ax.axhline(0, color="grey", lw=.8); ax.axvline(-.5, ls=":", color="k")
    ax.set_title(f"Event study: Region {r} ({lever} discount)")
    ax.set_xlabel("Weeks from 1 Mar 2023"); ax.set_ylabel("Treated-control gap in ln(orders)")
plt.tight_layout(); plt.savefig(FIG / "event_study.png", dpi=150); plt.close()

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax, (r, lever) in zip(axes, LEVERS):
    grid = np.linspace(-0.05, 0.15, 81)
    for cap, ls in [(None, "-"), (CAPACITY, "--")]:
        c = optimise.profit_curve(lever, res[lever]["base_q"], res[lever]["did"]["elasticity"], DIST[r], grid, cap)
        ax.plot(c.discount * 100, c.profit, ls, label=f"capacity = {cap}")
    ax.axvline(5, ls=":", color="k"); ax.set_yscale("log")
    ax.set_title(f"Region {r}: profit vs {lever} discount")
    ax.set_xlabel("Discount (%)"); ax.set_ylabel("Daily contribution ($, log scale)"); ax.legend()
plt.tight_layout(); plt.savefig(FIG / "profit_curves.png", dpi=150); plt.close()