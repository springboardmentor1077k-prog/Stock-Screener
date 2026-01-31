
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.stock import Stock
from app.models.fundamentals import Fundamentals

def init_db(db: Session) -> None:
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # specific seed data if needed
    user = db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("password"),
            is_superuser=True,
        )
        db.add(user)
        db.commit()

    # Seed stocks and fundamentals (Indian Stocks)
    if db.query(Stock).count() == 0:
        data = [
            
        ]
        
        for item in data:
            stock = Stock(
                symbol=item["symbol"],
                company_name=item["name"],
                sector=item["sector"],
                industry="n/a",
                exchange=item.get("exchange", "BSE"),
                market_cap=item["cap"],
                status="ACTIVE"
            )

            db.add(stock)
            db.flush() # flush to get stock.id
            
            fund = Fundamentals(
                stock_id=stock.id,
                market_cap=item["cap"],
                pe_ratio=item["pe"],
                div_yield=item["yield"]
            )
            db.add(fund)
            
        db.commit()
