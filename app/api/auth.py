from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from app.core.config import settings
from app.core.security import verify_password, create_access_token, get_password_hash
from app.db.mongodb import get_db

# 1. Initialize Router
router = APIRouter(prefix="/auth", tags=["auth"])

# 2. OAuth2 Scheme for dependency injection
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# 3. Dependency to get current user from JWT
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Accessing settings via dot notation
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        if username is None or role is None:
            raise credentials_exception
        return {"email": username, "role": role}
    except JWTError:
        raise credentials_exception

# 4. Registration Endpoint
@router.post("/register")
async def register(user_data: dict):
    db = get_db()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data["email"]})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )
    
    # Create new user document
    hashed_password = get_password_hash(user_data["password"])
    new_user = {
        "email": user_data["email"],
        "role": user_data["role"],
        "hashed_password": hashed_password,
        "active": True
    }
    
    await db.users.insert_one(new_user)
    return {"message": "User registered successfully"}

# 5. Login Endpoint (Returns JWT)
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_db()
    
    # Find user by email (OAuth2 uses 'username' field)
    user = await db.users.find_one({"email": form_data.username})
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password"
        )
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}