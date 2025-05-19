from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pkg.api import (
    router,
    recipient_router,
    volunteer_router,
    requirement_router,
    fund_router,
)
from pkg.database import Database
from pkg.middleware import PrintBodyMiddleware
from contextlib import asynccontextmanager

from pkg.utils import UPLOAD_PATH


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database("sqlite+aiosqlite:///database.db")
    await db.connect()
    app.state.db = db
    print("Database connected")
    yield
    await db.disconnect()
    print("Database disconnected")


app = FastAPI(lifespan=lifespan)
app.add_middleware(PrintBodyMiddleware)
app.include_router(
    router,
    prefix="/api",
    tags=["api"],
)
app.include_router(
    recipient_router,
    prefix="/api",
    tags=["recipient"],
)
app.include_router(
    volunteer_router,
    prefix="/api",
    tags=["volunteer"],
)
app.include_router(
    requirement_router,
    prefix="/api",
    tags=["requirement"],
)
app.include_router(
    fund_router,
    prefix="/api",
    tags=["fund"],
)

app.mount("/api/uploads", StaticFiles(directory=UPLOAD_PATH), name="uploads")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000, host="0.0.0.0")
