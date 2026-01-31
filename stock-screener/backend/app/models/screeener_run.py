
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class UserQuery(Base):
    __tablename__ = "user_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    raw_query_text = Column(Text, nullable=False)
    
    # Store parsed action and DSL for transparency/history
    action = Column(String)  # 'get_price', 'screen'
    parsed_dsl = Column(JSON) # The full DSL JSON
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="queries")
