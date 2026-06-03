from fastapi import FastAPI
from app.api.routes import health

app = FastAPI(title="GroupMark API")

app.include_router(health.router)

