# from fastapi import FastAPI
# from app.db.database import engine, Base
# import app.models

# from app.core.security import get_current_user
# from fastapi import Depends

# from app.api.screener import router as screener_router


# from app.api.auth import router as auth_router
# from app.api.market import router as market_router

# app = FastAPI()

# @app.on_event("startup") 
# def startup():
#     Base.metadata.create_all(bind=engine)

# app.include_router(auth_router)
# app.include_router(screener_router)
# app.include_router(market_router)

# @app.get("/protected")
# def protected_route(current_user = Depends(get_current_user)):
#     return {
#         "message": "You are authenticated",
#         "user": current_user.email
#     }
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from app.db.database import engine, Base
import app.models  # important for model discovery

from app.core.security import get_current_user

from app.api.auth import router as auth_router
from app.api.screener import router as screener_router
from app.api.market import router as market_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("🚀 Starting application...")
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic (optional)
    print("🛑 Shutting down application...")


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(screener_router)
app.include_router(market_router)


@app.get("/protected")
def protected_route(current_user=Depends(get_current_user)):
    return {
        "message": "You are authenticated",
        "user": current_user.email
    }