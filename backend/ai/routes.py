from fastapi import APIRouter, Depends, HTTPException
from backend.ai.engine import run_engine
from backend.auth import get_current_user_dependency

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/screener")
def screener(query: str, current_user=Depends(get_current_user_dependency)):
    try:
        dsl, results = run_engine(query)
        return {"dsl": dsl, "results": results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
