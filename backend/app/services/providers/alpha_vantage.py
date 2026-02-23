# import httpx
# from app.services.providers.base import MarketDataProvider
# from app.core.config import settings


# class AlphaVantageProvider(MarketDataProvider):

#     BASE_URL = "https://www.alphavantage.co/query"

#     async def fetch_fundamentals(self, symbol: str) -> dict:
#         # Add NSE suffix for Indian stocks
#         # formatted_symbol = f"{symbol}.NSE"
#          formatted_symbol = symbol 

#         params = {
#             "function": "OVERVIEW",
#             "symbol": formatted_symbol,
#             "apikey": settings.ALPHA_VANTAGE_API_KEY
#         }

#         async with httpx.AsyncClient() as client:
#             response = await client.get(self.BASE_URL, params=params)

#         if response.status_code != 200:
#             raise Exception("Alpha Vantage API failed")

#         data = response.json()
#         print("Alpha Vantage Response:", data)

#         # If empty or rate limited → trigger failover
#         if not data or "Note" in data or "Information" in data:
#             raise Exception("Alpha Vantage returned invalid or limited response")

#         return {
#             "symbol": data.get("Symbol"),
#             "name": data.get("Name"),
#             "pe_ratio": float(data.get("PERatio") or 0),
#             "peg_ratio": float(data.get("PEGRatio") or 0),
#             "market_cap": float(data.get("MarketCapitalization") or 0)
#         }

import httpx
from app.services.providers.base import MarketDataProvider
from app.core.config import settings


class AlphaVantageProvider(MarketDataProvider):

    BASE_URL = "https://www.alphavantage.co/query"

    async def fetch_fundamentals(self, symbol: str) -> dict:
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": settings.ALPHA_VANTAGE_API_KEY
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self.BASE_URL, params=params)

        if response.status_code != 200:
            raise Exception("Alpha Vantage API failed")

        data = response.json()
        print("Alpha Vantage Response:", data)

        if not data or "Note" in data or "Information" in data:
            raise Exception("Alpha Vantage returned invalid or limited response")

        return {
            "symbol": data.get("Symbol"),
            "name": data.get("Name"),
            "pe_ratio": float(data.get("PERatio") or 0),
            "peg_ratio": float(data.get("PEGRatio") or 0),
            "market_cap": float(data.get("MarketCapitalization") or 0)
        }