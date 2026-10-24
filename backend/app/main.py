from fastapi import FastAPI

from app.api.routes.users import router as users_router


app = FastAPI(
    title="Never Enough API",
    description="API commune au site web et aux applications mobiles.",
    version="0.1.0",
)

app.include_router(users_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}