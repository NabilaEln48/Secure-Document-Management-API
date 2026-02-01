from fastapi import FastAPI
from app.db.mongodb import connect_to_mongo, close_mongo_connection

# Point to the NEW file and NEW variable name
from app.api.auth import router as auth_router
from app.api.doc_manager import doc_router 

app = FastAPI(title="Secure Document Approval System")

app.include_router(auth_router)
app.include_router(doc_router)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"status": "online"}