from fastapi import FastAPI

app = FastAPI(title="Finance Tracker API", version="0.0.1")

@app.get("/health")
async def health_check() -> dict[str, str]:
    # API placeholder for now
    return {"status": "ok, I guess..."}