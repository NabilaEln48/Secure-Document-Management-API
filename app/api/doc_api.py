from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/test")
async def test_endpoint():
    return {"message": "Documents API is working"}