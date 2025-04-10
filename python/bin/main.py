from fastapi import FastAPI
from pkg.api import router


app = FastAPI()
app.include_router(
    router,
    prefix="/api",
    tags=["api"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000, host="0.0.0.0")
