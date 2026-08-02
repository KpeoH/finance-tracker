from fastapi import FastAPI

from app.api.routes import (
    auth_router,
    categories_router,
    transactions_router,
    users_router,
)

app = FastAPI(title="Finance Tracker API", version="0.0.1")

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(transactions_router)
