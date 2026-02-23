from abc import ABC, abstractmethod


class MarketDataProvider(ABC):

    @abstractmethod
    async def fetch_fundamentals(self, symbol: str) -> dict:
        pass