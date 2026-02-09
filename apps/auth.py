# app/auth.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from typing import Optional

from tools.tools import *

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

class MnemonicLoginRequest(BaseModel):
    mnemonic: str
    @validator('mnemonic')
    def validate_mnemonic(cls, v):
        words = v.strip().split()
        if len(words) != 12:
            raise ValueError('Mnemonic must be exactly 12 words')
        return v.strip()

class RegisterRequest(BaseModel):
    username: str
    @validator('username')
    def validate_username(cls, v):
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username must be at most 50 characters')
        return v

class UserResponse(BaseModel):
    user_id: str
    username: str
    has_messages: bool = False
    created_at: datetime
    last_seen: Optional[datetime]

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    username: str
    created_at: datetime
    expires_at: datetime

class MnemonicResponse(BaseModel):
    mnemonic: str
    user_id: str
    username: str

class UserListItem(BaseModel):
    user_id: str
    username: str
    last_seen: Optional[datetime]
    is_online: bool = False


templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def loginweb(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
    })

@router.get("/register", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("register.html", {
        "request": request,
    })


@router.post("/mnemonic_register", response_model=MnemonicResponse)
async def mnemonic_register(request: RegisterRequest, db: Session = Depends(get_db)):
    mnemonic = generate_mnemonic()
    seed = mnemonic_to_seed(mnemonic)
    user_id = derive_user_id_from_mnemonic(mnemonic)
    verification_hash = derive_verification_hash(seed)
    existing_user = db.query(User).filter(User.user_id == user_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    salt = secrets.token_bytes(32)
    encryption_key = derive_encryption_key(seed, salt)
    encrypted_username = encrypt_data(request.username, encryption_key)
    user = User(
        user_id=user_id,
        encrypted_username=encrypted_username,
        verification_hash=verification_hash,
        encryption_key_salt=base64.b64encode(salt).decode(),
        created_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return MnemonicResponse(mnemonic=mnemonic, user_id=user_id, username=request.username)

@router.post("/mnemonic_login", response_model=SessionResponse)
async def mnemonic_login(request: MnemonicLoginRequest, response: Response, db: Session = Depends(get_db)):
    seed = mnemonic_to_seed(request.mnemonic)
    user_id = derive_user_id_from_mnemonic(request.mnemonic)
    verification_hash = derive_verification_hash(seed)
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid mnemonic")
    if user.verification_hash != verification_hash:
        raise HTTPException(status_code=401, detail="Invalid mnemonic")
    user_data = get_user_with_decryption(db, user_id, seed)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid mnemonic")
    user.last_seen = datetime.now(timezone.utc)
    db.commit()
    session = create_session(db, user_id, seed)
    response.set_cookie(key="session_id", value=session.session_id, httponly=True, secure=True, samesite="lax", max_age=30*24*60*60)
    set_user_online(user_id)
    return SessionResponse(session_id=session.session_id, user_id=user_id, username=user_data["username"], created_at=session.created_at, expires_at=session.expires_at)

@router.post("/logout")
async def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    session = get_session_from_cookie(request, db)
    if session:
        set_user_offline(session.user_id)
        db.query(DBSession).filter(DBSession.session_id == session.session_id).delete()
        db.commit()
    response.delete_cookie("session_id")
    return {"message": "Logged out"}

@router.get("/session", response_model=SessionResponse)
async def get_session(request: Request, db: Session = Depends(get_db)):
    session = get_session_from_cookie(request, db)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return SessionResponse(session_id=session.session_id, user_id=session.user_id, username="[encrypted]", created_at=session.created_at, expires_at=session.expires_at)

@router.get("/users", response_model=list[UserListItem])
async def list_users(request: Request, db: Session = Depends(get_db)):
    session = get_session_from_cookie(request, db)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    users = db.query(User).all()
    return [UserListItem(user_id=u.user_id, username="[encrypted]", last_seen=u.last_seen, is_online=is_user_online(u.user_id)) for u in users]

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, request: Request, db: Session = Depends(get_db)):
    session = get_session_from_cookie(request, db)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(user_id=user.user_id, username="[encrypted]", has_messages=check_user_has_messages(db, user_id), created_at=user.created_at, last_seen=user.last_seen)

@router.get("/mnemonic", response_model=MnemonicResponse)
async def get_mnemonic_info(mnemonic: str, db: Session = Depends(get_db)):
    try:
        seed = mnemonic_to_seed(mnemonic)
        user_id = derive_user_id_from_mnemonic(mnemonic)
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = get_user_with_decryption(db, user_id, seed)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid mnemonic")
        return MnemonicResponse(mnemonic=mnemonic, user_id=user_id, username=user_data["username"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/validate/{user_id}")
async def validate_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    return {"exists": user is not None, "user_id": user_id}