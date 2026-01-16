from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: LoginRequest):
    if data.username == "admin" and data.password == "1234":
        return {"access_token": "token123"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/protected")
def protected(authorization: str = Header(None)):
    if authorization != "Bearer token123":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"message": "Success 🎉"}
