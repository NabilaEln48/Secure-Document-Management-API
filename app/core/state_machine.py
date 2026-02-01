from enum import Enum
from fastapi import HTTPException, status

class Role(str, Enum):
    UPLOADER = "UPLOADER"
    REVIEWER = "REVIEWER"
    APPROVER = "APPROVER"
    ADMIN = "ADMIN"

class State(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

# The transition matrix: (Current State, Target State) -> Required Role
ALLOWED_TRANSITIONS = {
    (State.DRAFT, State.SUBMITTED): Role.UPLOADER,
    (State.SUBMITTED, State.IN_REVIEW): Role.REVIEWER,
    (State.IN_REVIEW, State.APPROVED): Role.APPROVER,
    (State.IN_REVIEW, State.REJECTED): Role.APPROVER,
    (State.APPROVED, State.ARCHIVED): Role.ADMIN,
}

def validate_transition(current_state: State, target_state: State, user_role: Role):
    required_role = ALLOWED_TRANSITIONS.get((current_state, target_state))
    
    if not required_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from {current_state} to {target_state}."
        )
    
    if user_role != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user_role}' is not authorized to move document to {target_state}."
        )
    return True