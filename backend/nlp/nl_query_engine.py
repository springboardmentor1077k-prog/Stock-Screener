import re


class NLQueryEngine:
    def __init__(self):
        self.sector_map = {
            "tech": "Technology",
            "technology": "Technology",
            "finance": "Financials",
            "financials": "Financials",
            "health": "Health Care",
            "healthcare": "Health Care",
            "energy": "Energy",
            "consumer": "Consumer Discretionary",
        }
        self.reject_terms = [
            "predict",
            "forecast",
            "will",
            "should i",
            "buy",
            "sell",
            "recommend",
            "advise",
        ]

    def parse(self, text: str):
        t = (text or "").strip().lower()
        for rt in self.reject_terms:
            if rt in t:
                raise ValueError("Advice or forecasting queries are not supported")
        sector = None
        for key, norm in self.sector_map.items():
            if re.search(rf"\b{re.escape(key)}\b", t):
                sector = norm
                break
        numerics = []
        mcap_rules = self._extract_numeric(t, ["market cap", "mkt cap", "capitalization"], "market_cap_b")
        price_rules = self._extract_numeric(t, ["price"], "price")
        pe_rules = self._extract_numeric(t, ["pe", "p/e", "pe ratio"], "pe_ratio")
        numerics.extend(mcap_rules + price_rules + pe_rules)
        return {"sector": sector, "numerics": numerics}

    def _extract_numeric(self, text, keywords, field_name):
        ops = {
            ">": [">", "above", "over", "greater", "greater than", "gt", "more than", "exceed"],
            "<": ["<", "below", "under", "less", "less than", "lt", "under than", "underneath"],
        }
        found = []
        for kw in keywords:
            if kw in text:
                for sym, words in ops.items():
                    for w in words:
                        pat = rf"{re.escape(kw)}\s*{re.escape(w)}\s*([0-9]+(\.[0-9]+)?)"
                        m = re.search(pat, text)
                        if m:
                            val = float(m.group(1))
                            if field_name == "market_cap_b":
                                val = float(val)
                            found.append({"field": field_name, "op": sym, "value": val})
                num_pat = rf"{re.escape(kw)}\s*([0-9]+(\.[0-9]+)?)\s*(b|bn|billion)?"
                m2 = re.search(num_pat, text)
                if m2:
                    val = float(m2.group(1))
                    if field_name == "market_cap_b":
                        val = float(val)
                    found.append({"field": field_name, "op": ">=", "value": val})
        return found

