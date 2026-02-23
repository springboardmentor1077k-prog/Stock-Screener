# from sqlalchemy import Column, Integer, Float, ForeignKey
# from app.db.database import Base

# class Fundamentals(Base):
#     __tablename__ = "fundamentals"

#     id = Column(Integer, primary_key=True, index=True)
#     stock_id = Column(Integer, ForeignKey("stocks.id"))
#     pe_ratio = Column(Float)
#     peg_ratio = Column(Float)
#     promoter_holding = Column(Float)
from sqlalchemy import Column, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


class Fundamentals(Base):
    __tablename__ = "fundamentals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False)

    pe_ratio = Column(Float)
    peg_ratio = Column(Float)
    market_cap = Column(Float)

    fetched_at = Column(DateTime(timezone=True), server_default=func.now())