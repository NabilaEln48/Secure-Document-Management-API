import os
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException
from app.api.auth import get_current_user
from app.db.mongodb import get_db

doc_router = APIRouter(prefix="/documents", tags=["documents"])
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@doc_router.post("/")
async def create_document(
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # 1. Save the file physically
    file_path = os.path.join(UPLOAD_DIR, f"{datetime.utcnow().timestamp()}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Record it in MongoDB
    db = get_db()
    new_doc = {
        "title": title,
        "filename": file.filename,
        "path": file_path,
        "owner": current_user["email"],
        "status": "DRAFT",
        "created_at": datetime.utcnow()
    }
    result = await db.documents.insert_one(new_doc)
    
    return {
        "id": str(result.inserted_id),
        "message": f"Document '{title}' saved successfully!",
        "location": file_path
    }