# from sqlalchemy import Column, Integer, Float, ForeignKey
# from app.db.database import Base

# class QuarterlyFinancial(Base):
#     __tablename__ = "quarterly_financials"

#     id = Column(Integer, primary_key=True, index=True)
#     stock_id = Column(Integer, ForeignKey("stocks.id"))
#     year = Column(Integer)
#     quarter = Column(Integer)
#     revenue = Column(Float)
#     ebitda = Column(Float)
#     net_profit = Column(Float)

import uuid
from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base


class QuarterlyFinancials(Base):
    __tablename__ = "quarterly_financials"

    id = Column(Integer, primary_key=True, index=True)

    stock_id = Column(
        UUID(as_uuid=True),
        ForeignKey("stocks.id"),
        nullable=False
    )

    year = Column(Integer)
    quarter = Column(Integer)

    revenue = Column(Float)
    ebitda = Column(Float)
    net_profit = Column(Float)