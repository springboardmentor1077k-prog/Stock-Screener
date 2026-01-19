import os
import math
import datetime as dt
from typing import List, Dict, Any

SAMPLE = [
    {"ticker": "AAPL", "sector": "Information Technology", "peg": 2.1, "fcf": 90000000000.0, "debt": 98000000000.0, "target_low": 150.0, "price": 145.0, "rev_yoy": 0.04, "ebitda_yoy": 0.05, "next_earnings_days": 20, "buyback": True, "beats": 3},
    {"ticker": "MSFT", "sector": "Information Technology", "peg": 2.5, "fcf": 88000000000.0, "debt": 60000000000.0, "target_low": 360.0, "price": 355.0, "rev_yoy": 0.13, "ebitda_yoy": 0.12, "next_earnings_days": 25, "buyback": True, "beats": 4},
    {"ticker": "NVDA", "sector": "Information Technology", "peg": 1.9, "fcf": 24000000000.0, "debt": 10000000000.0, "target_low": 90.0, "price": 88.0, "rev_yoy": 0.50, "ebitda_yoy": 0.52, "next_earnings_days": 18, "buyback": True, "beats": 4},
    {"ticker": "AMD", "sector": "Information Technology", "peg": 2.8, "fcf": 4500000000.0, "debt": 2500000000.0, "target_low": 100.0, "price": 95.0, "rev_yoy": 0.20, "ebitda_yoy": 0.22, "next_earnings_days": 28, "buyback": True, "beats": 3},
    {"ticker": "QCOM", "sector": "Information Technology", "peg": 1.7, "fcf": 8000000000.0, "debt": 6000000000.0, "target_low": 130.0, "price": 128.0, "rev_yoy": 0.08, "ebitda_yoy": 0.09, "next_earnings_days": 10, "buyback": True, "beats": 3},
    {"ticker": "CSCO", "sector": "Information Technology", "peg": 2.0, "fcf": 14000000000.0, "debt": 10000000000.0, "target_low": 50.0, "price": 48.0, "rev_yoy": 0.03, "ebitda_yoy": 0.04, "next_earnings_days": 22, "buyback": True, "beats": 3},
]

def fcf_to_debt_ratio(fcf: float, debt: float) -> float:
    if debt <= 0:
        return math.inf
    return fcf / debt

def price_vs_target_condition(price: float, target_low: float, rule: str) -> bool:
    if rule == "<= target_low":
        return price <= target_low
    if rule == "<= target_mean":
        return price <= target_low
    return False

def sample_metrics() -> List[Dict[str, Any]]:
    return SAMPLE

def yf_metrics(tickers: List[str]) -> List[Dict[str, Any]]:
    try:
        import yfinance as yf
    except Exception:
        return SAMPLE
    out = []
    for t in tickers:
        try:
            y = yf.Ticker(t)
            info = getattr(y, "info", {}) or {}
            peg = info.get("pegRatio")
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            target_low = info.get("targetLowPrice") or info.get("targetMeanPrice")
            bs = y.balance_sheet
            debt = None
            if bs is not None and not bs.empty:
                td = [c for c in ["Total Debt", "Long Term Debt", "Short Long Term Debt"] if c in bs.index]
                if td:
                    debt = float(bs.loc[td[0]].iloc[0])
            cf = y.cashflow
            fcf = None
            if cf is not None and not cf.empty:
                ocf = cf.loc["Operating Cash Flow"].iloc[0] if "Operating Cash Flow" in cf.index else None
                capex = cf.loc["Capital Expenditure"].iloc[0] if "Capital Expenditure" in cf.index else None
                if ocf is not None and capex is not None:
                    fcf = float(ocf) + float(capex)
            fin = y.financials
            rev_yoy = None
            ebitda_yoy = None
            if fin is not None and not fin.empty:
                if "Total Revenue" in fin.index and len(fin.loc["Total Revenue"].values) >= 2:
                    v = fin.loc["Total Revenue"].values
                    rev_yoy = (float(v[0]) - float(v[1])) / float(v[1]) if float(v[1]) != 0 else None
                if "EBITDA" in fin.index and len(fin.loc["EBITDA"].values) >= 2:
                    v = fin.loc["EBITDA"].values
                    ebitda_yoy = (float(v[0]) - float(v[1])) / float(v[1]) if float(v[1]) != 0 else None
            cal = y.calendar
            next_days = None
            try:
                if cal is not None and "Earnings Date" in cal.index:
                    d = cal.loc["Earnings Date"].iloc[0]
                    if hasattr(d, "to_pydatetime"):
                        d = d.to_pydatetime()
                    if isinstance(d, dt.date):
                        next_days = (d - dt.datetime.utcnow().date()).days
            except Exception:
                next_days = None
            sector = info.get("sector")
            buyback = False
            beats = None
            if all(v is not None for v in [peg, price, target_low, fcf, debt, rev_yoy, ebitda_yoy, next_days, sector]):
                out.append({
                    "ticker": t,
                    "sector": sector,
                    "peg": float(peg),
                    "fcf": float(fcf),
                    "debt": float(debt),
                    "target_low": float(target_low),
                    "price": float(price),
                    "rev_yoy": float(rev_yoy),
                    "ebitda_yoy": float(ebitda_yoy),
                    "next_earnings_days": int(next_days),
                    "buyback": buyback,
                    "beats": beats or 0
                })
        except Exception:
            continue
    return out or SAMPLE

def screen(companies: List[Dict[str, Any]], dsl: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for c in companies:
        if c.get("sector") != dsl.get("industry_category"):
            continue
        if c.get("peg") is None or c["peg"] > dsl["filters"]["peg_ratio_max"]:
            continue
        if fcf_to_debt_ratio(c.get("fcf", 0.0), c.get("debt", 0.0)) < dsl["filters"]["fcf_to_debt_min"]:
            continue
        if not price_vs_target_condition(c.get("price", 0.0), c.get("target_low", 0.0), dsl["filters"]["price_vs_target"]):
            continue
        if dsl["filters"]["revenue_yoy_positive"] and c.get("rev_yoy", 0.0) <= 0:
            continue
        if dsl["filters"]["ebitda_yoy_positive"] and c.get("ebitda_yoy", 0.0) <= 0:
            continue
        if dsl["filters"]["earnings_beat_likely"] and c.get("beats", 0) < 3:
            continue
        if dsl["filters"]["buyback_announced"] and not c.get("buyback", False):
            continue
        if c.get("next_earnings_days", 999) > dsl["filters"]["next_earnings_within_days"]:
            continue
        out.append({
            "ticker": c["ticker"],
            "peg": c["peg"],
            "fcf_to_debt": fcf_to_debt_ratio(c["fcf"], c["debt"]),
            "price": c["price"],
            "target_low": c["target_low"],
            "rev_yoy": c["rev_yoy"],
            "ebitda_yoy": c["ebitda_yoy"],
            "earnings_within_days": c["next_earnings_days"],
            "buyback": c["buyback"]
        })
    return out