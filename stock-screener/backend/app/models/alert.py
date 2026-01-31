
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Alert(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False)
    
    target_price = Column(Float, nullable=False)
    condition = Column(String, nullable=False) # "Above" or "Below"

    user = relationship("User", backref="alerts")
    stock = relationship("Stock", back_populates="alerts")
