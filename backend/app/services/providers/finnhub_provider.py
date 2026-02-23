import httpx
from app.services.providers.base import MarketDataProvider
from app.core.config import settings


class FinnhubProvider(MarketDataProvider):

    BASE_URL = "https://finnhub.io/api/v1"

    async def fetch_fundamentals(self, symbol: str) -> dict:
        headers = {
            "X-Finnhub-Token": settings.FINNHUB_API_KEY
        }

        async with httpx.AsyncClient(timeout=10) as client:

            # Company profile
            profile_resp = await client.get(
                f"{self.BASE_URL}/stock/profile2",
                params={"symbol": symbol},
                headers=headers
            )

            # Basic financials
            metrics_resp = await client.get(
                f"{self.BASE_URL}/stock/metric",
                params={"symbol": symbol, "metric": "all"},
                headers=headers
            )

        if profile_resp.status_code != 200 or metrics_resp.status_code != 200:
            raise Exception("Finnhub API failed")

        profile = profile_resp.json()
        metrics = metrics_resp.json()

        if not profile:
            raise Exception("Finnhub returned empty profile")

        metric_data = metrics.get("metric", {})

        return {
            "symbol": symbol,
            "name": profile.get("name"),
            "pe_ratio": metric_data.get("peNormalizedAnnual", 0),
            "peg_ratio": metric_data.get("pegRatio", 0),
            "market_cap": profile.get("marketCapitalization", 0)
        }