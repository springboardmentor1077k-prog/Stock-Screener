@echo off
cd backend
uvicorn app.main:app --reload --port 8000