import json
import os
from typing import Dict, Any
from . import market_data

def run(dsl: Dict[str, Any], data_source: str = "sample") -> Dict[str, Any]:
    if data_source == "yfinance":
        tickers = ["AAPL","MSFT","NVDA","AMD","QCOM","CSCO","ORCL","IBM","INTC","TXN","AVGO"]
        companies = market_data.yf_metrics(tickers)
    else:
        companies = market_data.sample_metrics()
    results = market_data.screen(companies, dsl)
    return {"count": len(results), "items": results}

def save_outputs(results: Dict[str, Any], json_path: str, csv_path: str):
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    if results.get("items"):
        import csv
        keys = list(results["items"][0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for row in results["items"]:
                w.writerow(row)