from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from routes.customer import router as customer_router
from routes.brief import router as brief_router
from routes.bill_delta import router as bill_delta_router
from routes.intent import router as intent_router
from routes.transcribe import router as transcribe_router
from routes.execute import router as execute_router
from routes.pah_check import router as pah_router
from websocket.execution_ws import router as ws_router

app = FastAPI(title="T-Rep AI — Agent Assist API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customer_router,   prefix="/customer",   tags=["customer"])
app.include_router(brief_router,      prefix="/brief",      tags=["brief"])
app.include_router(bill_delta_router, prefix="/bill-delta", tags=["bill-delta"])
app.include_router(intent_router,     prefix="/intent",     tags=["intent"])
app.include_router(transcribe_router, prefix="/transcribe", tags=["transcribe"])
app.include_router(execute_router,    prefix="/execute",    tags=["execute"])
app.include_router(pah_router,        prefix="/pah-check",  tags=["pah"])
app.include_router(ws_router)


@app.get("/health")
def health():
    return {"status": "ok"}
