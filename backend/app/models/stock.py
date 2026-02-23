# from sqlalchemy import Column, Integer, String
# from app.db.database import Base

# class Stock(Base):
#     __tablename__ = "stocks"

#     id = Column(Integer, primary_key=True, index=True)
#     symbol = Column(String, unique=True, index=True)
#     name = Column(String)
#     sector = Column(String)
#     exchange = Column(String)

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    exchange = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())