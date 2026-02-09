from fastapi import APIRouter, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone, timedelta
import secrets
import hashlib
import base64

from mnemonic import Mnemonic
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
from db.db import get_db, set_user_online, set_user_offline, is_user_online
from db.models import User, Message, UserSession, Conversation

def generate_session_id() -> str:
    return secrets.token_urlsafe(24)[:32]

def generate_mnemonic() -> str:
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=128)

def mnemonic_to_seed(mnemonic: str) -> bytes:
    mnemo = Mnemonic("english")
    if not mnemo.check(mnemonic):
        raise ValueError("Invalid mnemonic phrase")
    return mnemo.to_seed(mnemonic)

def derive_encryption_key(seed: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
    key = kdf.derive(seed)
    return base64.urlsafe_b64encode(key)

def derive_user_id_from_mnemonic(mnemonic: str) -> str:
    seed = mnemonic_to_seed(mnemonic)
    return hashlib.sha256(seed).hexdigest()[:16]

def derive_verification_hash(seed: bytes) -> str:
    return hashlib.sha256(seed).hexdigest()

def encrypt_data(data: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()

def hash_session_key(seed: bytes) -> str:
    return hashlib.sha256(seed).hexdigest()

def create_session(db: Session, user_id: str, seed: bytes) -> UserSession:
    session_id = generate_session_id()
    session = UserSession(
        session_id=session_id,
        user_id=user_id,
        encryption_key_hash=hash_session_key(seed),
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        last_activity=datetime.now(timezone.utc)
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_session_from_cookie(request: Request, db: Session) -> Optional[UserSession]:
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    session = db.query(UserSession).filter(UserSession.session_id == session_id, UserSession.expires_at > datetime.now(timezone.utc)).first()
    if session:
        session.last_activity = datetime.now(timezone.utc)
        db.commit()
    return session

def get_user_with_decryption(db: Session, user_id: str, seed: bytes) -> Optional[dict]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None
    salt = base64.b64decode(user.encryption_key_salt)
    encryption_key = derive_encryption_key(seed, salt)
    try:
        username = decrypt_data(user.encrypted_username, encryption_key)
    except:
        return None
    return {"user": user, "username": username}

def check_user_has_messages(db: Session, user_id: str) -> bool:
    return db.query(Message).filter((Message.sender_id == user_id) | (Message.recipient_id == user_id)).count() > 0


def generate_message_id() -> str:
    return secrets.token_urlsafe(12)[:16]

def get_or_create_conversation(db: Session, user_id: str, other_user_id: str) -> Conversation:
    conv = db.query(Conversation).filter(
        Conversation.user_id == user_id,
        Conversation.other_user_id == other_user_id
    ).first()
    
    if not conv:
        conv = Conversation(
            user_id=user_id,
            other_user_id=other_user_id,
            unread_count=0
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    
    return conv

def update_conversation(db: Session, message: Message):
    sender_conv = get_or_create_conversation(db, message.sender_id, message.recipient_id)
    sender_conv.last_message_id = message.message_id
    sender_conv.last_message_timestamp = message.timestamp
    
    recipient_conv = get_or_create_conversation(db, message.recipient_id, message.sender_id)
    recipient_conv.last_message_id = message.message_id
    recipient_conv.last_message_timestamp = message.timestamp
    recipient_conv.unread_count += 1
    
    db.commit()



