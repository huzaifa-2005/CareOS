from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

from app.routes.whatsapp import router as whatsapp_router
app.include_router(whatsapp_router)

