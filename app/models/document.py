import os
import shutil
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse

# --- CRITICAL: ROUTER MUST BE INITIALIZED BEFORE PROJECT IMPORTS ---
router = APIRouter(prefix="/documents", tags=["documents"])

# --- NOW PROJECT IMPORTS ---
from app.db.mongodb import get_db
from app.models.document import DocumentDB
from app.core.state_machine import State, Role, validate_transition
from app.services.audit import create_audit_entry
from app.api.auth import get_current_user

# --- CONFIGURATION ---
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx"
}

# --- HELPERS ---
async def update_document_state(doc_id: str, old_state: State, new_state: State, user: dict, comment: str = None):
    db = get_db()
    validate_transition(old_state, new_state, user["role"])
    
    update_result = await db.documents.update_one(
        {"_id": ObjectId(doc_id)},
        {
            "$set": {"current_state": new_state, "updated_at": datetime.utcnow()},
            "$inc": {"version": 1}
        }
    )
    
    if update_result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Database update failed")

    await create_audit_entry(doc_id, old_state, new_state, user["email"], user["role"], comment)
    return {"message": f"Status updated to {new_state}"}

# --- ENDPOINTS ---

@router.post("/", response_model=DocumentDB)
async def create_document(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    if current_user["role"] != Role.UPLOADER:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    if file.content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_path = os.path.join(UPLOAD_DIR, f"{datetime.utcnow().timestamp()}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db = get_db()
    doc_dict = {
        "title": title,
        "description": description,
        "filename": file.filename,
        "file_path": file_path,
        "content_type": file.content_type,
        "owner_id": current_user["email"],
        "current_state": State.DRAFT,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "version": 1
    }
    
    result = await db.documents.insert_one(doc_dict)
    doc_dict["_id"] = str(result.inserted_id)
    
    await create_audit_entry(doc_dict["_id"], None, State.DRAFT, current_user["email"], current_user["role"], "Initial Upload")
    return doc_dict

@router.get("/{id}/download")
async def download_document(id: str, user=Depends(get_current_user)):
    doc = await get_db().documents.find_one({"_id": ObjectId(id)})
    if not doc: 
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(path=doc["file_path"], filename=doc["filename"], media_type=doc["content_type"])

@router.post("/{id}/submit")
async def submit(id: str, user=Depends(get_current_user)):
    doc = await get_db().documents.find_one({"_id": ObjectId(id)})
    return await update_document_state(id, doc["current_state"], State.SUBMITTED, user)

@router.post("/{id}/review")
async def review(id: str, user=Depends(get_current_user)):
    doc = await get_db().documents.find_one({"_id": ObjectId(id)})
    return await update_document_state(id, doc["current_state"], State.IN_REVIEW, user)

@router.post("/{id}/approve")
async def approve(id: str, user=Depends(get_current_user), comment: str = "Approved"):
    doc = await get_db().documents.find_one({"_id": ObjectId(id)})
    return await update_document_state(id, doc["current_state"], State.APPROVED, user, comment)

@router.get("/{id}/history")
async def get_document_history(id: str, user=Depends(get_current_user)):
    db = get_db()
    history = await db.document_versions.find({"document_id": id}).sort("timestamp", 1).to_list(None)
    for entry in history:
        entry["_id"] = str(entry["_id"])
    return history