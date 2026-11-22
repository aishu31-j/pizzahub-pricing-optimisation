"""Difference-in-differences, event-study and robustness estimators."""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

LOG_PRICE_CHANGE = np.log(1 - 0.05)   # ln(0.95): the size of the price shock


def did_log(sample: pd.DataFrame):
    """ln(Q) = a + b*treat + g*post + d*(treat x post), HC3 robust errors.

    delta = log change in orders caused by the 5% discount; delta / ln(0.95)
    converts it to an arc elasticity with respect to the discounted price.
    """
    m = smf.ols("log_q ~ treat * post", sample).fit(cov_type="HC3")
    d, se = m.params["treat:post"], m.bse["treat:post"]
    return {
        "model": m, "delta": d, "delta_se": se,
        "elasticity": d / LOG_PRICE_CHANGE,
        "elasticity_ci": ((d + 1.96 * se) / LOG_PRICE_CHANGE,
                          (d - 1.96 * se) / LOG_PRICE_CHANGE),
    }


def did_poisson(sample: pd.DataFrame):
    """Count-data robustness check: Poisson DiD with robust errors."""
    m = smf.poisson("qty ~ treat * post", sample).fit(disp=0, cov_type="HC1")
    d, se = m.params["treat:post"], m.bse["treat:post"]
    return {"model": m, "delta": d, "delta_se": se, "elasticity": d / LOG_PRICE_CHANGE}


def pretrend_test(sample: pd.DataFrame):
    """Pre-period only: does the treated group trend differently? (HC3)"""
    pre = sample[sample["post"] == 0].copy()
    pre["t"] = (pre["date"] - pre["date"].min()).dt.days / 7.0
    m = smf.ols("log_q ~ treat * t", pre).fit(cov_type="HC3")
    return {"coef": m.params["treat:t"], "p": m.pvalues["treat:t"]}


def placebo_did(sample: pd.DataFrame, fake_date="2023-02-01"):
    """DiD on pre-period data with a fake policy date. Should be ~0."""
    pre = sample[sample["post"] == 0].copy()
    pre["post"] = (pre["date"] >= pd.Timestamp(fake_date)).astype(int)
    m = smf.ols("log_q ~ treat * post", pre).fit(cov_type="HC3")
    return {"coef": m.params["treat:post"], "p": m.pvalues["treat:post"]}


def event_study(sample: pd.DataFrame, ref_week=-1):
    """Weekly leads/lags of the treated-vs-control gap in ln(Q), relative to ref_week."""
    s = sample.copy()
    s["week"] = ((s["date"] - pd.Timestamp("2023-03-01")).dt.days // 7).astype(int)
    f = f"log_q ~ treat + C(week) + treat:C(week, Treatment(reference={ref_week}))"
    m = smf.ols(f, s).fit(cov_type="HC3")
    rows = [(ref_week, 0.0, 0.0)]
    for name, b in m.params.items():
        if name.startswith("treat:C(week"):
            wk = int(name.split("[T.")[1].rstrip("]"))
            rows.append((wk, b, m.bse[name]))
    return pd.DataFrame(rows, columns=["week", "coef", "se"]).sort_values("week")