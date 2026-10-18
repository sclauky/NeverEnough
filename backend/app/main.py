from fastapi import FastAPI

app = FastAPI(
    title="Never Enough API",
    description="API commune au site web et aux applications mobiles.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}