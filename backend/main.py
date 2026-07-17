from fastapi import FastAPI
from app.routes.whatsapp import router as whatsapp_router

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(whatsapp_router)

