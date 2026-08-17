import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, chat, matches, statistics
from app.core.init_db import init_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend host
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(matches.router, prefix=f"{settings.API_V1_STR}/matches", tags=["matches"])
app.include_router(statistics.router, prefix=f"{settings.API_V1_STR}/stats", tags=["stats"])

@app.on_event("startup")
async def startup_event():
    print("Starting up CricketGPT backend...")
    # Auto-initialize and seed DB
    await init_db()

@app.get("/")
def read_root():
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
