from fastapi import FastAPI
from pkg.api import router
from pkg.database import Database
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database("sqlite+aiosqlite:///database.db")
    await db.connect()
    app.state.db = db
    print("db connected")
    yield
    await db.disconnect()
    print("Database disconnected")


app = FastAPI(lifespan=lifespan)
app.include_router(
    router,
    prefix="/api",
    tags=["api"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000, host="0.0.0.0")
