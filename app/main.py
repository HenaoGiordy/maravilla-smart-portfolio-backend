from fastapi import FastAPI

from app.interfaces.http.routes.market_data import router as market_data_router


app = FastAPI(
    title="Maravilla Smart Portfolio Backend",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(market_data_router, prefix="/api/v1")