import random
from datetime import datetime, timedelta
from database.connection import get_db_connection


# ============================================================================
# IT SECTOR SUB-CATEGORIES (NOT Consulting - Products & Services focused)
# ============================================================================

IT_SUB_SECTORS = {
    "Semiconductor": {
        "prefixes": ["Micro", "Semi", "Chip", "Nano", "Quantum", "Silicon", "Logic", "Power", "Analog", "Digital", 
                     "Crystal", "Photon", "Amp", "Wave", "Circuit", "Electron", "Ion", "Laser", "Optic", "Volt"],
        "suffixes": ["Devices", "Semiconductor", "Microsystems", "Chips", "Electronics", "Components", "Silicon", 
                     "Logic", "Tech", "Circuits", "Systems", "Dynamics", "Solutions", "Innovations"],
        "companies": [
            ("NVDA", "NVIDIA Corp", 875.50), ("AMD", "Advanced Micro Devices", 178.45),
            ("INTC", "Intel Corp", 42.80), ("QCOM", "Qualcomm Inc", 168.75),
            ("TSM", "Taiwan Semiconductor", 142.50), ("AVGO", "Broadcom Inc", 1285.50),
            ("TXN", "Texas Instruments", 172.40), ("MRVL", "Marvell Tech", 68.25),
            ("MU", "Micron Technology", 95.80), ("LRCX", "Lam Research", 785.40),
            ("AMAT", "Applied Materials", 185.60), ("KLAC", "KLA Corp", 625.30),
            ("ON", "ON Semiconductor", 72.45), ("ADI", "Analog Devices", 198.50),
            ("NXPI", "NXP Semiconductors", 235.80), ("SWKS", "Skyworks Solutions", 108.25),
            ("MCHP", "Microchip Technology", 85.40), ("MPWR", "Monolithic Power", 625.80),
            ("CRUS", "Cirrus Logic", 98.50), ("SLAB", "Silicon Labs", 142.30),
        ]
    },
    "Enterprise Software": {
        "prefixes": ["Soft", "Code", "Dev", "App", "Data", "Smart", "Auto", "Net", "Flow", "Sync",
                     "Link", "Hub", "Core", "Base", "Prime", "Stack", "Node", "Grid", "Matrix", "Vertex"],
        "suffixes": ["Software", "Systems", "Solutions", "Technologies", "Labs", "Works", "Logic", "Ware",
                     "Suite", "Platform", "Apps", "Code", "Dev", "Pro", "Enterprise"],
        "companies": [
            ("MSFT", "Microsoft Corp", 378.25), ("ORCL", "Oracle Corp", 125.40),
            ("CRM", "Salesforce Inc", 298.50), ("ADBE", "Adobe Inc", 575.80),
            ("NOW", "ServiceNow Inc", 785.25), ("INTU", "Intuit Inc", 625.80),
            ("WDAY", "Workday Inc", 265.40), ("SNPS", "Synopsys Inc", 545.60),
            ("CDNS", "Cadence Design", 285.75), ("TEAM", "Atlassian Corp", 225.40),
            ("ANSS", "ANSYS Inc", 328.50), ("PTC", "PTC Inc", 175.40),
            ("MANH", "Manhattan Associates", 215.60), ("SSNC", "SS&C Technologies", 68.25),
            ("HUBS", "HubSpot Inc", 585.40), ("ZEN", "Zendesk Inc", 78.50),
        ]
    },
    "Cloud Computing": {
        "prefixes": ["Cloud", "Azure", "Nimbus", "Stratus", "Sky", "Virtual", "Flex", "Scale", "Elastic", "Stream",
                     "Vapor", "Cumulus", "Cirrus", "Aero", "Mist", "Fog", "Rain", "Storm", "Thunder", "Breeze"],
        "suffixes": ["Cloud", "Hosting", "Services", "Platform", "Infrastructure", "Networks", "Compute",
                     "Stack", "Grid", "Mesh", "Fabric", "Space", "Zone", "Hub"],
        "companies": [
            ("AMZN", "Amazon Web Services", 178.35), ("GOOGL", "Google Cloud", 141.80),
            ("SNOW", "Snowflake Inc", 185.60), ("MDB", "MongoDB Inc", 385.60),
            ("NET", "Cloudflare Inc", 85.45), ("DOCN", "DigitalOcean Holdings", 42.80),
            ("TWLO", "Twilio Inc", 65.80), ("DBX", "Dropbox Inc", 28.45),
            ("BOX", "Box Inc", 28.60), ("ESTC", "Elastic NV", 115.40),
            ("CFLT", "Confluent Inc", 32.80), ("SUMO", "Sumo Logic", 12.50),
        ]
    },
    "Computer Hardware": {
        "prefixes": ["Hard", "Tech", "Core", "Prime", "Nova", "Ultra", "Hyper", "Max", "Pro", "Elite",
                     "Apex", "Peak", "Titan", "Alpha", "Omega", "Delta", "Sigma", "Beta", "Gamma", "Zeta"],
        "suffixes": ["Hardware", "Systems", "Computers", "Technologies", "Devices", "Equipment", "Machines",
                     "Computing", "Dynamics", "Electronics", "Components", "Works"],
        "companies": [
            ("AAPL", "Apple Inc", 178.50), ("HPQ", "HP Inc", 32.45),
            ("HPE", "Hewlett Packard Enterprise", 18.25), ("DELL", "Dell Technologies", 115.80),
            ("LOGI", "Logitech International", 82.50), ("WDC", "Western Digital", 52.40),
            ("STX", "Seagate Technology", 85.60), ("NTAP", "NetApp Inc", 95.25),
            ("PSTG", "Pure Storage", 42.80), ("SMCI", "Super Micro Computer", 285.60),
            ("CRSR", "Corsair Gaming", 15.80), ("HEAR", "Turtle Beach", 12.50),
        ]
    },
    "Telecom Equipment": {
        "prefixes": ["Tele", "Comm", "Link", "Net", "Wire", "Signal", "Wave", "Beam", "Connect", "Global",
                     "Trans", "Relay", "Pulse", "Echo", "Sonic", "Radio", "Broad", "Fiber", "Spectrum", "Band"],
        "suffixes": ["Communications", "Telecom", "Networks", "Wireless", "Systems", "Connect", "Link",
                     "Comms", "Technologies", "Solutions", "Global", "International"],
        "companies": [
            ("CSCO", "Cisco Systems", 52.35), ("JNPR", "Juniper Networks", 38.45),
            ("NOK", "Nokia Corp", 4.25), ("ERIC", "Ericsson", 5.80),
            ("LITE", "Lumentum Holdings", 52.40), ("VIAV", "Viavi Solutions", 12.80),
            ("COMM", "CommScope Holding", 8.50), ("CIEN", "Ciena Corp", 52.40),
            ("INFN", "Infinera Corp", 6.80), ("CALX", "Calix Inc", 48.50),
        ]
    },
    "Cybersecurity": {
        "prefixes": ["Cyber", "Secure", "Guard", "Shield", "Defend", "Safe", "Trust", "Vault", "Crypto", "Fire",
                     "Lock", "Fort", "Wall", "Armor", "Hawk", "Eagle", "Sentinel", "Watch", "Alert", "Protect"],
        "suffixes": ["Security", "Defense", "Protection", "Guard", "Shield", "Systems", "Cyber",
                     "Safe", "Secure", "Lock", "Wall", "Net", "Tech"],
        "companies": [
            ("PANW", "Palo Alto Networks", 315.80), ("CRWD", "CrowdStrike Holdings", 285.40),
            ("ZS", "Zscaler Inc", 195.75), ("FTNT", "Fortinet Inc", 68.50),
            ("OKTA", "Okta Inc", 95.25), ("S", "SentinelOne", 25.80),
            ("CYBR", "CyberArk Software", 245.60), ("TENB", "Tenable Holdings", 48.25),
            ("VRNS", "Varonis Systems", 52.40), ("QLYS", "Qualys Inc", 165.80),
            ("RPD", "Rapid7 Inc", 48.50), ("SAIL", "SailPoint Technologies", 58.40),
        ]
    },
    "Data Center & Infrastructure": {
        "prefixes": ["Data", "Center", "Core", "Hub", "Node", "Server", "Rack", "Compute", "Edge", "Grid",
                     "Power", "Cool", "Host", "Vault", "Storage", "Archive", "Cache", "Buffer", "Stack", "Cluster"],
        "suffixes": ["Data", "Centers", "Infrastructure", "Services", "Systems", "Technologies",
                     "Hosting", "Storage", "Power", "Networks", "Solutions"],
        "companies": [
            ("VRT", "Vertiv Holdings", 58.25), ("DLR", "Digital Realty", 142.80),
            ("EQIX", "Equinix Inc", 785.40), ("AKAM", "Akamai Technologies", 115.25),
            ("NEWR", "New Relic", 85.40), ("DOMO", "Domo Inc", 12.80),
            ("FIVN", "Five9 Inc", 78.50), ("ZI", "ZoomInfo Technologies", 18.50),
        ]
    },
    "AI & Machine Learning": {
        "prefixes": ["AI", "Neural", "Deep", "Smart", "Cognitive", "Intel", "Learn", "Vision", "Auto", "Mind",
                     "Brain", "Think", "Reason", "Logic", "Pattern", "Predict", "Insight", "Sense", "Model", "Agent"],
        "suffixes": ["AI", "Intelligence", "Learning", "Analytics", "Systems", "Labs", "Tech",
                     "Minds", "Logic", "Vision", "Sense", "Brain", "Neural"],
        "companies": [
            ("PLTR", "Palantir Technologies", 22.85), ("AI", "C3.ai Inc", 32.45),
            ("PATH", "UiPath Inc", 18.50), ("BBAI", "BigBear.ai", 2.85),
            ("SOUN", "SoundHound AI", 5.40), ("UPST", "Upstart Holdings", 35.60),
            ("RXRX", "Recursion Pharmaceuticals", 12.50), ("VEEV", "Veeva Systems", 185.40),
        ]
    },
    "Fintech & Payments": {
        "prefixes": ["Pay", "Fin", "Cash", "Money", "Credit", "Trans", "Swift", "Quick", "Fast", "Instant",
                     "Digital", "Mobile", "Smart", "Secure", "Trust", "Clear", "Settle", "Fund", "Wealth", "Trade"],
        "suffixes": ["Pay", "Finance", "Payments", "Financial", "Money", "Cash", "Credit",
                     "Tech", "Systems", "Solutions", "Services", "Global"],
        "companies": [
            ("SQ", "Block Inc", 72.45), ("PYPL", "PayPal Holdings", 68.25),
            ("FIS", "Fidelity National Info", 68.40), ("FISV", "Fiserv Inc", 145.60),
            ("GPN", "Global Payments", 128.50), ("AFRM", "Affirm Holdings", 42.80),
            ("SOFI", "SoFi Technologies", 8.50), ("HOOD", "Robinhood Markets", 12.50),
            ("COIN", "Coinbase Global", 185.40), ("NU", "Nu Holdings", 12.80),
        ]
    },
    "Networking & Communications": {
        "prefixes": ["Net", "Link", "Connect", "Route", "Switch", "Hub", "Mesh", "Fiber", "Wire", "Band",
                     "Path", "Bridge", "Gate", "Port", "Channel", "Stream", "Flow", "Pipe", "Trunk", "Line"],
        "suffixes": ["Networks", "Networking", "Connect", "Systems", "Solutions", "Technologies",
                     "Communications", "Link", "Net", "Comm", "Global"],
        "companies": [
            ("ANET", "Arista Networks", 285.40), ("FFIV", "F5 Inc", 175.80),
            ("UI", "Ubiquiti Inc", 185.60), ("EXTR", "Extreme Networks", 25.40),
            ("NTGR", "NETGEAR Inc", 18.50), ("RBBN", "Ribbon Communications", 3.50),
        ]
    },
    "Gaming & Interactive": {
        "prefixes": ["Game", "Play", "Quest", "Epic", "Hero", "Battle", "Arena", "Zone", "World", "Realm",
                     "Pixel", "Bit", "Render", "Frame", "Unity", "Stream", "Live", "Fun", "Joy", "Thrill"],
        "suffixes": ["Games", "Gaming", "Interactive", "Entertainment", "Studios", "Media",
                     "Play", "Quest", "Digital", "Tech", "Software"],
        "companies": [
            ("TTWO", "Take-Two Interactive", 165.40), ("EA", "Electronic Arts", 142.50),
            ("RBLX", "Roblox Corp", 42.80), ("U", "Unity Software", 28.50),
            ("PLTK", "Playtika Holding", 8.50), ("SKLZ", "Skillz Inc", 1.50),
        ]
    },
    "Internet Services": {
        "prefixes": ["Web", "Net", "Online", "Digital", "Virtual", "Cyber", "Click", "Search", "Browse", "Surf",
                     "Portal", "Site", "Page", "Link", "Social", "Share", "Post", "Chat", "Meet", "Connect"],
        "suffixes": ["Web", "Internet", "Online", "Digital", "Net", "Media", "Social",
                     "Connect", "Link", "Hub", "Portal", "Platform"],
        "companies": [
            ("META", "Meta Platforms", 485.20), ("SNAP", "Snap Inc", 12.50),
            ("PINS", "Pinterest Inc", 32.40), ("DASH", "DoorDash Inc", 115.40),
            ("UBER", "Uber Technologies", 68.50), ("LYFT", "Lyft Inc", 15.80),
            ("ABNB", "Airbnb Inc", 145.60), ("BKNG", "Booking Holdings", 3650.80),
        ]
    },
}


def generate_company_names(sub_sector_info, count, existing_symbols):
    """Generate unique company names for a sub-sector."""
    companies = []
    prefixes = sub_sector_info["prefixes"]
    suffixes = sub_sector_info["suffixes"]
    
    used_names = set()
    attempts = 0
    
    while len(companies) < count and attempts < count * 15:
        attempts += 1
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        
        # Create variations
        variations = [
            f"{prefix}{suffix}",
            f"{prefix} {suffix}",
            f"{prefix}{suffix} Inc",
            f"{prefix}{suffix} Corp",
            f"{prefix}{suffix} Technologies",
            f"{prefix} {suffix} Holdings",
            f"{prefix}{suffix} Group",
            f"{prefix} Systems {suffix}",
            f"{prefix} {suffix} Ltd",
            f"{prefix}{suffix} International",
        ]
        
        name = random.choice(variations)
        if name not in used_names:
            used_names.add(name)
            # Generate a unique symbol (3-5 chars)
            symbol_base = f"{prefix[:2].upper()}{suffix[:2].upper()}"
            symbol = f"{symbol_base}{random.randint(1, 99):02d}"
            while symbol in existing_symbols:
                symbol = f"{prefix[:2].upper()}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(1, 999):03d}"
            existing_symbols.add(symbol)
            base_price = random.uniform(5, 800)
            companies.append((symbol, name, base_price))
    
    return companies


def generate_stock_data(symbol, name, base_price, sub_sector):
    """
    Generate comprehensive stock data matching all search criteria:
    1. IT sector (not consulting) ✓
    2. PEG ratio < 3 (varies)
    3. Debt to FCF >= 0.25 (can repay debt in 4 years or less) (varies)
    4. Price near/below analyst targets (varies)
    5. Revenue & EBITDA growing Y-o-Y (varies)
    6. Likely to beat earnings (varies)
    7. Has buyback announced (varies)
    8. Earnings within 30 days (varies)
    """
    
    # Base metrics with variation
    price = round(base_price * random.uniform(0.85, 1.15), 2)
    change = round(random.uniform(-5.5, 6.5), 2)
    
    # PE Ratio (tech typically 15-65)
    pe_ratio = round(random.uniform(10, 70), 2)
    
    # Market Cap (millions)
    market_cap = round(random.uniform(200, 600000), 2)
    
    # Promoter holding
    promoter = round(random.uniform(15, 80), 2)
    
    # Has Buyback - weighted towards more buybacks for variety (45%)
    has_buyback = random.random() < 0.45
    
    # Revenue Growth (legacy field)
    revenue_growth = round(random.uniform(-10, 55), 2)
    
    # Quarterly Earnings (positive bias for healthy IT companies)
    positive_bias = 0.82
    q1 = round(random.uniform(10, 1000) if random.random() < positive_bias else random.uniform(-150, 1000), 2)
    q2 = round(random.uniform(10, 1000) if random.random() < positive_bias else random.uniform(-150, 1000), 2)
    q3 = round(random.uniform(10, 1000) if random.random() < positive_bias else random.uniform(-150, 1000), 2)
    q4 = round(random.uniform(10, 1000) if random.random() < positive_bias else random.uniform(-150, 1000), 2)
    
    eps = round((q1 + q2 + q3 + q4) / 100, 2)
    
    # Dividend Yield (tech typically lower)
    dividend_yield = round(random.uniform(0, 2.8), 2)
    
    # Debt to Equity
    debt_to_equity = round(random.uniform(0.05, 2.5), 2)
    
    # ROE
    roe = round(random.uniform(3, 45), 2)
    
    # Exchange
    exchange = random.choice(["NSE", "NSE", "NSE", "BSE"])
    
    # ========== NEW CRITERIA FIELDS ==========
    
    # PEG Ratio = PE / Earnings Growth Rate
    # Distribution: ~60% < 3 (attractive), ~40% >= 3
    earnings_growth_rate = round(random.uniform(3, 50), 2)
    if pe_ratio > 0 and earnings_growth_rate > 0:
        peg_ratio = round(pe_ratio / earnings_growth_rate, 2)
    else:
        peg_ratio = round(random.uniform(0.4, 5.0), 2)
    
    # Adjust PEG to create better distribution
    if random.random() < 0.60:  # 60% chance of attractive PEG
        peg_ratio = round(random.uniform(0.3, 2.9), 2)
    else:
        peg_ratio = round(random.uniform(3.0, 6.0), 2)
    
    # Free Cash Flow (millions)
    free_cash_flow = round(random.uniform(20, 20000), 2)
    
    # Total Debt and Debt to FCF ratio
    # User wants debt_to_fcf >= 0.25 (meaning FCF/Debt >= 0.25, can repay in 4 years)
    # So debt_to_fcf should be <= 4 years for this criteria
    # Distribution: ~55% can repay in 4 years or less
    if random.random() < 0.55:
        debt_to_fcf = round(random.uniform(0.2, 3.9), 2)  # Can repay in <4 years
    else:
        debt_to_fcf = round(random.uniform(4.0, 10.0), 2)  # Takes >4 years
    
    total_debt = round(free_cash_flow * debt_to_fcf, 2)
    
    # Analyst Price Targets
    # Create variety: some below low, some near low, some mid, some near high, some above
    target_spread = random.uniform(0.15, 0.45)  # 15-45% spread
    analyst_price_avg = round(price * random.uniform(0.85, 1.45), 2)
    analyst_price_low = round(analyst_price_avg * (1 - target_spread), 2)
    analyst_price_high = round(analyst_price_avg * (1 + target_spread), 2)
    
    # Price vs Target positioning with good distribution
    position_roll = random.random()
    if position_roll < 0.20:  # 20% Below Low
        price = round(analyst_price_low * random.uniform(0.75, 0.98), 2)
        price_vs_target = "Below Low"
    elif position_roll < 0.40:  # 20% Near Low
        price = round(analyst_price_low * random.uniform(0.99, 1.12), 2)
        price_vs_target = "Near Low"
    elif position_roll < 0.65:  # 25% Mid Range
        mid = (analyst_price_low + analyst_price_high) / 2
        price = round(mid * random.uniform(0.92, 1.08), 2)
        price_vs_target = "Mid Range"
    elif position_roll < 0.85:  # 20% Near High
        price = round(analyst_price_high * random.uniform(0.88, 1.02), 2)
        price_vs_target = "Near High"
    else:  # 15% Above High
        price = round(analyst_price_high * random.uniform(1.02, 1.25), 2)
        price_vs_target = "Above High"
    
    # Revenue & EBITDA Growth Y-o-Y
    # ~70% growing (positive), ~30% shrinking
    if random.random() < 0.70:
        revenue_growth_yoy = round(random.uniform(2, 55), 2)
        ebitda_growth_yoy = round(random.uniform(1, 50), 2)
    else:
        revenue_growth_yoy = round(random.uniform(-25, 2), 2)
        ebitda_growth_yoy = round(random.uniform(-30, 1), 2)
    
    # EBITDA (millions)
    ebitda = round(random.uniform(10, 12000), 2)
    
    # Earnings Estimates
    estimated_eps = round(eps * random.uniform(0.85, 1.25), 2)
    historical_beat_rate = round(random.uniform(25, 98), 2)
    
    # Likely to beat: higher chance if historical beat rate is high
    likely_to_beat = (historical_beat_rate > 60 and random.random() < 0.75) or random.random() < 0.35
    
    # Next Earnings Date
    today = datetime.now()
    # Distribution: ~40% within 30 days, ~60% outside
    if random.random() < 0.40:
        days_until_earnings = random.randint(1, 30)
    else:
        days_until_earnings = random.randint(31, 90)
    
    next_earnings_date = today + timedelta(days=days_until_earnings)
    earnings_within_30_days = days_until_earnings <= 30
    
    return {
        "symbol": symbol,
        "company_name": name,
        "sector": "Information Technology",
        "sub_sector": sub_sector,
        "price": price,
        "change_pct": change,
        "pe_ratio": pe_ratio,
        "market_cap": market_cap,
        "promoter_holding": promoter,
        "has_buyback": has_buyback,
        "revenue_growth": revenue_growth,
        "q1_earnings": q1,
        "q2_earnings": q2,
        "q3_earnings": q3,
        "q4_earnings": q4,
        "eps": eps,
        "dividend_yield": dividend_yield,
        "debt_to_equity": debt_to_equity,
        "roe": roe,
        "exchange": exchange,
        "peg_ratio": peg_ratio,
        "earnings_growth_rate": earnings_growth_rate,
        "free_cash_flow": free_cash_flow,
        "total_debt": total_debt,
        "debt_to_fcf": debt_to_fcf,
        "analyst_price_low": analyst_price_low,
        "analyst_price_high": analyst_price_high,
        "analyst_price_avg": analyst_price_avg,
        "price_vs_target": price_vs_target,
        "revenue_growth_yoy": revenue_growth_yoy,
        "ebitda": ebitda,
        "ebitda_growth_yoy": ebitda_growth_yoy,
        "estimated_eps": estimated_eps,
        "historical_beat_rate": historical_beat_rate,
        "likely_to_beat": likely_to_beat,
        "next_earnings_date": next_earnings_date.strftime("%Y-%m-%d"),
        "earnings_within_30_days": earnings_within_30_days,
    }


def seed_and_update_stocks():
    """Seed database with 500 IT sector company stocks."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    all_stocks = []
    existing_symbols = set()
    
    # 1. Add real company stocks first
    for sub_sector, info in IT_SUB_SECTORS.items():
        for symbol, name, base_price in info["companies"]:
            if symbol not in existing_symbols:
                existing_symbols.add(symbol)
                stock_data = generate_stock_data(symbol, name, base_price, sub_sector)
                all_stocks.append(stock_data)
    
    print(f"Added {len(all_stocks)} real company stocks")
    
    # 2. Generate additional stocks to reach 500
    target_count = 500
    remaining = target_count - len(all_stocks)
    stocks_per_sector = remaining // len(IT_SUB_SECTORS) + 1
    
    for sub_sector, info in IT_SUB_SECTORS.items():
        generated = generate_company_names(info, stocks_per_sector, existing_symbols)
        for symbol, name, base_price in generated:
            if len(all_stocks) < target_count:
                stock_data = generate_stock_data(symbol, name, base_price, sub_sector)
                all_stocks.append(stock_data)
    
    # Fill any remaining spots
    while len(all_stocks) < target_count:
        sub_sector = random.choice(list(IT_SUB_SECTORS.keys()))
        info = IT_SUB_SECTORS[sub_sector]
        generated = generate_company_names(info, 5, existing_symbols)
        for symbol, name, base_price in generated:
            if len(all_stocks) < target_count:
                stock_data = generate_stock_data(symbol, name, base_price, sub_sector)
                all_stocks.append(stock_data)
    
    print(f"Total stocks to insert: {len(all_stocks)}")
    
    # 3. Create "ideal" stocks that match ALL user criteria
    # PEG < 3, debt_to_fcf < 4, price near/below low, revenue/ebitda growing, 
    # likely to beat, has buyback, earnings within 30 days
    ideal_count = 75  # ~15% of stocks will match all criteria
    for i in range(min(ideal_count, len(all_stocks))):
        stock = all_stocks[i]
        stock["peg_ratio"] = round(random.uniform(0.4, 2.8), 2)
        stock["debt_to_fcf"] = round(random.uniform(0.3, 3.8), 2)
        stock["total_debt"] = round(stock["free_cash_flow"] * stock["debt_to_fcf"], 2)
        stock["price_vs_target"] = random.choice(["Below Low", "Near Low"])
        stock["price"] = round(stock["analyst_price_low"] * random.uniform(0.80, 1.08), 2)
        stock["revenue_growth_yoy"] = round(random.uniform(5, 45), 2)
        stock["ebitda_growth_yoy"] = round(random.uniform(3, 40), 2)
        stock["likely_to_beat"] = True
        stock["historical_beat_rate"] = round(random.uniform(68, 96), 2)
        stock["has_buyback"] = True
        stock["earnings_within_30_days"] = True
        stock["next_earnings_date"] = (datetime.now() + timedelta(days=random.randint(3, 28))).strftime("%Y-%m-%d")
    
    # 4. Insert all stocks into database
    count = 0
    for stock in all_stocks:
        try:
            cur.execute("""
                INSERT INTO stocks (
                    symbol, company_name, sector, sub_sector, price, change_pct, pe_ratio,
                    market_cap, promoter_holding, has_buyback, revenue_growth,
                    q1_earnings, q2_earnings, q3_earnings, q4_earnings,
                    eps, dividend_yield, debt_to_equity, roe, exchange,
                    peg_ratio, earnings_growth_rate, free_cash_flow, total_debt, debt_to_fcf,
                    analyst_price_low, analyst_price_high, analyst_price_avg, price_vs_target,
                    revenue_growth_yoy, ebitda, ebitda_growth_yoy,
                    estimated_eps, historical_beat_rate, likely_to_beat,
                    next_earnings_date, earnings_within_30_days
                )
                VALUES (
                    %(symbol)s, %(company_name)s, %(sector)s, %(sub_sector)s, %(price)s, %(change_pct)s, %(pe_ratio)s,
                    %(market_cap)s, %(promoter_holding)s, %(has_buyback)s, %(revenue_growth)s,
                    %(q1_earnings)s, %(q2_earnings)s, %(q3_earnings)s, %(q4_earnings)s,
                    %(eps)s, %(dividend_yield)s, %(debt_to_equity)s, %(roe)s, %(exchange)s,
                    %(peg_ratio)s, %(earnings_growth_rate)s, %(free_cash_flow)s, %(total_debt)s, %(debt_to_fcf)s,
                    %(analyst_price_low)s, %(analyst_price_high)s, %(analyst_price_avg)s, %(price_vs_target)s,
                    %(revenue_growth_yoy)s, %(ebitda)s, %(ebitda_growth_yoy)s,
                    %(estimated_eps)s, %(historical_beat_rate)s, %(likely_to_beat)s,
                    %(next_earnings_date)s, %(earnings_within_30_days)s
                )
                ON CONFLICT (symbol) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    sector = EXCLUDED.sector,
                    sub_sector = EXCLUDED.sub_sector,
                    price = EXCLUDED.price,
                    change_pct = EXCLUDED.change_pct,
                    pe_ratio = EXCLUDED.pe_ratio,
                    market_cap = EXCLUDED.market_cap,
                    promoter_holding = EXCLUDED.promoter_holding,
                    has_buyback = EXCLUDED.has_buyback,
                    revenue_growth = EXCLUDED.revenue_growth,
                    q1_earnings = EXCLUDED.q1_earnings,
                    q2_earnings = EXCLUDED.q2_earnings,
                    q3_earnings = EXCLUDED.q3_earnings,
                    q4_earnings = EXCLUDED.q4_earnings,
                    eps = EXCLUDED.eps,
                    dividend_yield = EXCLUDED.dividend_yield,
                    debt_to_equity = EXCLUDED.debt_to_equity,
                    roe = EXCLUDED.roe,
                    exchange = EXCLUDED.exchange,
                    peg_ratio = EXCLUDED.peg_ratio,
                    earnings_growth_rate = EXCLUDED.earnings_growth_rate,
                    free_cash_flow = EXCLUDED.free_cash_flow,
                    total_debt = EXCLUDED.total_debt,
                    debt_to_fcf = EXCLUDED.debt_to_fcf,
                    analyst_price_low = EXCLUDED.analyst_price_low,
                    analyst_price_high = EXCLUDED.analyst_price_high,
                    analyst_price_avg = EXCLUDED.analyst_price_avg,
                    price_vs_target = EXCLUDED.price_vs_target,
                    revenue_growth_yoy = EXCLUDED.revenue_growth_yoy,
                    ebitda = EXCLUDED.ebitda,
                    ebitda_growth_yoy = EXCLUDED.ebitda_growth_yoy,
                    estimated_eps = EXCLUDED.estimated_eps,
                    historical_beat_rate = EXCLUDED.historical_beat_rate,
                    likely_to_beat = EXCLUDED.likely_to_beat,
                    next_earnings_date = EXCLUDED.next_earnings_date,
                    earnings_within_30_days = EXCLUDED.earnings_within_30_days;
            """, stock)
            count += 1
        except Exception as e:
            print(f"Error inserting {stock['symbol']}: {e}")
    
    conn.commit()
    print(f"✅ Database seeded with {count} IT sector stocks!")
    
    # Print summary stats
    cur.execute("SELECT COUNT(*) FROM stocks WHERE peg_ratio < 3")
    peg_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stocks WHERE debt_to_fcf <= 4")
    debt_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stocks WHERE price_vs_target IN ('Below Low', 'Near Low')")
    price_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stocks WHERE revenue_growth_yoy > 0 AND ebitda_growth_yoy > 0")
    growth_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stocks WHERE likely_to_beat = TRUE")
    beat_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stocks WHERE has_buyback = TRUE")
    buyback_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stocks WHERE earnings_within_30_days = TRUE")
    earnings_count = cur.fetchone()[0]
    
    # Count stocks matching ALL criteria
    cur.execute("""
        SELECT COUNT(*) FROM stocks 
        WHERE peg_ratio < 3 
        AND debt_to_fcf <= 4 
        AND price_vs_target IN ('Below Low', 'Near Low')
        AND revenue_growth_yoy > 0 
        AND ebitda_growth_yoy > 0
        AND likely_to_beat = TRUE
        AND has_buyback = TRUE
        AND earnings_within_30_days = TRUE
    """)
    all_criteria_count = cur.fetchone()[0]
    
    print(f"\n📊 Stock Distribution Stats (out of {count} stocks):")
    print(f"   PEG < 3: {peg_count}")
    print(f"   Debt/FCF <= 4 (can repay in 4 years): {debt_count}")
    print(f"   Price at/below low target: {price_count}")
    print(f"   Revenue & EBITDA growing Y-o-Y: {growth_count}")
    print(f"   Likely to beat estimates: {beat_count}")
    print(f"   Has buyback announced: {buyback_count}")
    print(f"   Earnings within 30 days: {earnings_count}")
    print(f"\n🎯 Stocks matching ALL criteria: {all_criteria_count}")
    
    # Show sub-sector distribution
    cur.execute("SELECT sub_sector, COUNT(*) FROM stocks GROUP BY sub_sector ORDER BY COUNT(*) DESC")
    print(f"\n📂 Sub-sector Distribution:")
    for row in cur.fetchall():
        print(f"   {row[0]}: {row[1]}")
    
    cur.close()
    conn.close()


def seed_sample_portfolio():
    """Seed sample portfolio data with realistic IT stock holdings."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Clear existing portfolio
    cur.execute("DELETE FROM portfolio")
    
    # Sample IT stock holdings across different strategies
    holdings = [
        ("Growth", "NVDA", 50, 450.00),
        ("Growth", "MSFT", 100, 320.00),
        ("Growth", "GOOGL", 75, 125.00),
        ("Growth", "AMD", 150, 120.00),
        ("Growth", "CRWD", 40, 200.00),
        ("Value", "AAPL", 200, 150.00),
        ("Value", "INTC", 300, 35.00),
        ("Value", "CSCO", 250, 45.00),
        ("Value", "QCOM", 80, 140.00),
        ("Tech Growth", "CRM", 80, 250.00),
        ("Tech Growth", "ADBE", 60, 500.00),
        ("Tech Growth", "NOW", 40, 700.00),
        ("Tech Growth", "PANW", 50, 280.00),
        ("Semiconductor", "AVGO", 30, 1000.00),
        ("Semiconductor", "TSM", 100, 120.00),
    ]
    
    for portfolio_name, symbol, shares, avg_price in holdings:
        cur.execute("""
            INSERT INTO portfolio (portfolio_name, symbol, shares, avg_buy_price)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (portfolio_name, symbol, shares, avg_price))
    
    conn.commit()
    print("✅ Sample portfolio seeded with 15 IT stock holdings!")
    cur.close()
    conn.close()


def seed_sample_alerts():
    """Seed sample alerts for common IT stocks."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Clear existing alerts
    cur.execute("DELETE FROM alerts")
    
    alerts = [
        ("NVDA", "P/E Ratio", "<", 50.00),
        ("NVDA", "Current Price", ">", 1000.00),
        ("MSFT", "Current Price", ">", 400.00),
        ("AAPL", "Current Price", "<", 160.00),
        ("AMD", "P/E Ratio", "<", 35.00),
        ("GOOGL", "Current Price", ">", 150.00),
        ("INTC", "Current Price", ">", 50.00),
        ("CRM", "P/E Ratio", "<", 70.00),
    ]
    
    for symbol, metric, condition, threshold in alerts:
        cur.execute("""
            INSERT INTO alerts (symbol, metric, condition, threshold)
            VALUES (%s, %s, %s, %s)
        """, (symbol, metric, condition, threshold))
    
    conn.commit()
    print("✅ Sample alerts seeded!")
    cur.close()
    conn.close()


if __name__ == "__main__":
    print("🚀 Seeding database with 500 IT sector stocks...")
    print("=" * 60)
    seed_and_update_stocks()
    seed_sample_portfolio()
    seed_sample_alerts()
    print("\n" + "=" * 60)
    print("✅ All data seeded successfully!")
