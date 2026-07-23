from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.whatsapp import router as whatsapp_router
from app.routes.web_chat import router as web_chat_router
from app.routes.receptionist_dashboard import router as receptionist_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://care-os-web-chat.vercel.app",
        "https://care-os-receptionist-dashboard.vercel.app",
        "http://localhost:5500",
        "http://localhost:5501",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:5501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(whatsapp_router)
app.include_router(web_chat_router)
app.include_router(receptionist_router)