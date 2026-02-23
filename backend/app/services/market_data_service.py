from app.services.providers.finnhub_provider import FinnhubProvider
from app.services.providers.alpha_vantage import AlphaVantageProvider
from app.services.cache_service import CacheService

from app.db.database import SessionLocal
from app.models.stock import Stock
from app.models.fundamentals import Fundamentals


class MarketDataService:

    def __init__(self):
        self.primary = FinnhubProvider()
        self.secondary = AlphaVantageProvider()
        self.cache = CacheService()

    async def fetch_with_failover(self, symbol: str) -> dict:

        cache_key = f"fundamentals:{symbol}"

        # 1️⃣ Check Cache First
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 2️⃣ Fetch from provider
        try:
            print("Using Finnhub")
            data = await self.primary.fetch_fundamentals(symbol)
        except Exception as e:
            print("Primary failed:", e)
            print("Switching to Alpha Vantage")
            data = await self.secondary.fetch_fundamentals(symbol)

        # 3️⃣ Save to DB
        db = SessionLocal()
        try:
            stock = db.query(Stock).filter(Stock.symbol == symbol).first()

            if not stock:
                stock = Stock(
                    symbol=symbol,
                    name=data.get("name"),
                    exchange=data.get("exchange")
                )
                db.add(stock)
                db.commit()
                db.refresh(stock)

            fundamentals = db.query(Fundamentals).filter(
                Fundamentals.stock_id == stock.id
            ).first()

            if not fundamentals:
                fundamentals = Fundamentals(
                    stock_id=stock.id,
                    pe_ratio=data.get("pe_ratio"),
                    peg_ratio=data.get("peg_ratio"),
                    market_cap=data.get("market_cap")
                )
                db.add(fundamentals)
            else:
                fundamentals.pe_ratio = data.get("pe_ratio")
                fundamentals.peg_ratio = data.get("peg_ratio")
                fundamentals.market_cap = data.get("market_cap")

            db.commit()
        finally:
            db.close()

        # 4️⃣ Store in Cache (5 min TTL)
        self.cache.set(cache_key, data, ttl=300)

        return data