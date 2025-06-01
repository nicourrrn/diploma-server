from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pkg.api import (
    recipient_router,
    volunteer_router,
    requirement_router,
    fund_router,
    profile_router,
)
from pkg.database import Database, DatabasePg
from pkg.middleware import PrintBodyMiddleware
from contextlib import asynccontextmanager

from pkg.utils import UPLOAD_PATH
import dotenv
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    dotenv.load_dotenv()
    logging.info("Connecting to the database...")
    pg_db = os.getenv("DATABASE_URL", None)
    if pg_db:
        db = DatabasePg(pg_db)
    else:
        logging.info("Using SQLite database")
    db = Database("sqlite+aiosqlite:///database.db")
    await db.connect()
    await db.create_tables()
    app.state.db = db
    logging.info("Database connected")
    yield
    await db.disconnect()
    logging.info("Database disconnected")


app = FastAPI(lifespan=lifespan)
app.add_middleware(PrintBodyMiddleware)
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_PATH), name="uploads")
app.include_router(
    profile_router,
    prefix="/api",
    tags=["profile"],
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000, host="0.0.0.0")
