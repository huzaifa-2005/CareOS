from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.whatsapp import router as whatsapp_router
from app.routes.web_chat import router as web_chat_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your Vercel domain once deployed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(whatsapp_router)
app.include_router(web_chat_router)