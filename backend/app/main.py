from fastapi import FastAPI

from app.api.routes import auth_router, users_router

app = FastAPI(title="Finance Tracker API", version="0.0.1")

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    # API placeholder for now
    return {"status": "ok, I guess..."}
