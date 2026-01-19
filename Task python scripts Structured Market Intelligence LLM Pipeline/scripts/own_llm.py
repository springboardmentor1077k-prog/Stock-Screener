import json
from typing import Dict, Any
from . import nlp_to_dsl
from . import market_data

def answer(query: str) -> Dict[str, Any]:
    dsl = nlp_to_dsl.generate_dsl(query, provider="local")
    companies = market_data.sample_metrics()
    screened = market_data.screen(companies, dsl)
    return {"query": query, "dsl": dsl, "recommendations": screened}

def run_cli():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--query", type=str, required=True)
    p.add_argument("--out", type=str, default="output/own_llm.json")
    args = p.parse_args()
    res = answer(args.query)
    import os
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    run_cli()