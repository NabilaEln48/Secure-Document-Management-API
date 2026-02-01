from datetime import datetime
from app.db.mongodb import get_db
from app.core.state_machine import State, Role

async def create_audit_entry(
    doc_id: str, 
    from_state: State, 
    to_state: State, 
    user_id: str, 
    user_role: Role, 
    comment: str = None
):
    db = get_db()
    audit_entry = {
        "document_id": doc_id,
        "from_state": from_state,
        "to_state": to_state,
        "changed_by": user_id,
        "role": user_role,
        "comment": comment,
        "timestamp": datetime.utcnow()
    }
    # This goes to the immutable document_versions collection
    await db.document_versions.insert_one(audit_entry)