def global_disclaimer():
    return "This platform provides informational market data only. Not investment advice. Markets involve risk."

def banner_disclaimer():
    return "Disclaimer: Informational use only. No recommendations. Please do your own research."

def screener_disclaimer():
    return "Screener insights are informational and do not constitute investment recommendations."

def analyst_disclaimer():
    return "Analyst targets are third-party opinions. Not advice. May be inaccurate or outdated."

def alerts_disclaimer():
    return "Alerts notify condition matches. They are not trading signals or advice."

def portfolio_disclaimer():
    return "Portfolio values are estimates based on last known market prices. Performance is not guaranteed."

def dashboard_disclaimer():
    return "Market data displayed on the dashboard may be delayed. For informational purposes only."

def compliance_level(level):
    if level == "low":
        return "Compliance Level: Low (Data display)"
    if level == "medium":
        return "Compliance Level: Medium (Analyst tools / screener)"
    if level == "high":
        return "Compliance Level: High (Advisory content)"
    if level == "very_high":
        return "Compliance Level: Very High (Portfolio management)"
    return "Compliance Level: Unclassified"
