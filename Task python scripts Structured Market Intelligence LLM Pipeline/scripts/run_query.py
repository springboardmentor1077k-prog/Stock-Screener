import argparse
import json
from pathlib import Path
from . import nlp_to_dsl
from . import screener_engine

DEFAULT_QUERY = (
    "Information technology companies with PEG < 3, debt to free cash flow ratio "
    "of at least 25%, price at or below analyst low target, revenue and EBITDA "
    "growing year over year, likely to beat next earnings, announced buybacks, "
    "and next earnings within 30 days."
)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--query", type=str, default=DEFAULT_QUERY)
    p.add_argument("--provider", type=str, default="local")
    p.add_argument("--data-source", type=str, default="sample")
    p.add_argument("--out", type=str, default="output")
    args = p.parse_args()
    dsl = nlp_to_dsl.generate_dsl(args.query, provider=args.provider)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    dsl_path = out_dir / "dsl.json"
    nlp_to_dsl.save_json(dsl, str(dsl_path))
    print(json.dumps(dsl, indent=2))
    results = screener_engine.run(dsl, data_source=args.data_source)
    json_path = out_dir / "results.json"
    csv_path = out_dir / "results.csv"
    screener_engine.save_outputs(results, str(json_path), str(csv_path))
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()