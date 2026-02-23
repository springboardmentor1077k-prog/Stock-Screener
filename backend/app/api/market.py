from fastapi import APIRouter
from app.services.market_data_service import MarketDataService

router = APIRouter(prefix="/market", tags=["Market"])

service = MarketDataService()

@router.post("/ingest/{symbol}")
async def ingest_symbol(symbol: str):
    data = await service.fetch_with_failover(symbol)
    return data