# app/chats.py
from fastapi import APIRouter, HTTPException, Request, Depends, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List, Optional
from datetime import datetime, timezone
import secrets
import json
from db.db import get_db, set_typing_status, get_typing_users, add_message_to_queue, get_queued_messages
from db.models import Message, Conversation, User
from tools import *

router = APIRouter(
    prefix="/chat",
    tags=["chats"],
)

templates = Jinja2Templates(directory="templates")


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                self.disconnect(user_id)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except:
                disconnected.append(user_id)
        for user_id in disconnected:
            self.disconnect(user_id)

manager = ConnectionManager()

class MessageCreateRequest(BaseModel):
    recipient_id: str
    encrypted_content: str
    encrypted_metadata: Optional[str] = None
    thread_id: Optional[str] = None
    
    @validator('recipient_id')
    def validate_recipient(cls, v):
        if len(v) != 16:
            raise ValueError('Invalid recipient_id')
        return v
    
    @validator('encrypted_content')
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Content cannot be empty')
        return v

class MessageResponse(BaseModel):
    message_id: str
    sender_id: str
    recipient_id: str
    encrypted_content: str
    encrypted_metadata: Optional[str]
    timestamp: datetime
    read_status: bool
    thread_id: Optional[str]

class ConversationResponse(BaseModel):
    user_id: str
    other_user_id: str
    last_message_id: Optional[str]
    last_message_timestamp: Optional[datetime]
    unread_count: int
    encrypted_summary: Optional[str]

class UnreadCountResponse(BaseModel):
    total_unread: int
    conversations: List[dict]

@router.get("/", response_class=HTMLResponse)
async def chat(request: Request):
    return templates.TemplateResponse("chat.html", {
        "request": request,
    })

@router.get("/list", response_class=HTMLResponse)
async def chatlist(request: Request):
    return templates.TemplateResponse("chatlist.html", {
        "request": request,
    })

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(request: Request, db: Session = Depends(get_db)):
    session = get_session_from_cookie(request, db)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    conversations = db.query(Conversation).filter(
        Conversation.user_id == session.user_id
    ).order_by(desc(Conversation.last_message_timestamp)).all()
    
    return [ConversationResponse(
        user_id=conv.user_id,
        other_user_id=conv.other_user_id,
        last_message_id=conv.last_message_id,
        last_message_timestamp=conv.last_message_timestamp,
        unread_count=conv.unread_count,
        encrypted_summary=conv.encrypted_summary
    ) for conv in conversations]

@router.get("/conversations/{other_user_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    other_user_id: str,
    request: Request,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    session = get_session_from_cookie(request, db)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if len(other_user_id) != 16:
        raise HTTPException(status_code=400, detail="Invalid user_id")
    
    messages = db.query(Message).filter(
        or_(
            and_(Message.sender_id == session.user_id, Message.recipient_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.recipient_id == session.user_id)
        )
    ).order_by(desc(Message.timestamp)).limit(limit).offset(offset).all()
    
    return [MessageResponse(
        message_id=msg.message_id,
        sender_id=msg.sender_id,
        recipient_id=msg.recipient_id,
        encrypted_content=msg.encrypted_content,
        encrypted_metadata=msg.encrypted_metadata,
        timestamp=msg.timestamp,
        read_status=msg.read_status,
        thread_id=msg.thread_id
    ) for msg in reversed(messages)]

@router.post("/messages", response_model=MessageResponse)
async def send_message(
    message_req: MessageCreateRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    session = get_session_from_cookie(request, db)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if message_req.recipient_id == session.user_id:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")
    
    recipient = db.query(User).filter(User.user_id == message_req.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    message = Message(
        message_id=generate_message_id(),
        sender_id=session.user_id,
        recipient_id=message_req.recipient_id,
        encrypted_content=message_req.encrypted_content,
        encrypted_metadata=message_req.encrypted_metadata,
        timestamp=datetime.now(timezone.utc),
        read_status=False,
        thread_id=message_req.thread_id
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    update_conversation(db, message)
    
    message_data = {
        "type": "new_message",
        "message": {
            "message_id": message.message_id,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "encrypted_content": message.encrypted_content,
            "encrypted_metadata": message.encrypted_metadata,
            "timestamp": message.timestamp.isoformat(),
            "read_status": message.read_status,
            "thread_id": message.thread_id
        }
    }
    
    await manager.send_personal_message(message_data, message_req.recipient_id)
    
    return MessageResponse(
        message_id=message.message_id,
        sender_id=message.sender_id,
        recipient_id=message.recipient_id,
        encrypted_content=message.encrypted_content,
        encrypted_metadata=message.encrypted_metadata,
        timestamp=message.timestamp,
        read_status=message.read_status,
        thread_id=message.thread_id
    )

@router.put("/messages/{message_id}/read")
async def mark_message_read(
    message_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    session = get_session_from_cookie(request, db)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if len(message_id) != 16:
        raise HTTPException(status_code=400, detail="Invalid message_id")
    
    message = db.query(Message).filter(
        Message.message_id == message_id,
        Message.recipient_id == session.user_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if not message.read_status:
        message.read_status = True
        
        conv = db.query(Conversation).filter(
            Conversation.user_id == session.user_id,
            Conversation.other_user_id == message.sender_id
        ).first()
        
        if conv and conv.unread_count > 0:
            conv.unread_count -= 1
        
        db.commit()
    
    return {"message": "Message marked as read", "message_id": message_id}

@router.get("/messages/unread", response_model=UnreadCountResponse)
async def get_unread_count(request: Request, db: Session = Depends(get_db)):
    session = get_session_from_cookie(request, db)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    conversations = db.query(Conversation).filter(
        Conversation.user_id == session.user_id,
        Conversation.unread_count > 0
    ).all()
    
    total_unread = sum(conv.unread_count for conv in conversations)
    
    conv_list = [
        {
            "other_user_id": conv.other_user_id,
            "unread_count": conv.unread_count
        }
        for conv in conversations
    ]
    
    return UnreadCountResponse(
        total_unread=total_unread,
        conversations=conv_list
    )

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    user_id = None
    
    try:
        auth_message = await websocket.receive_json()
        
        if auth_message.get("type") != "auth":
            await websocket.send_json({"type": "error", "message": "Authentication required"})
            await websocket.close()
            return
        
        session_id = auth_message.get("session_id")
        if not session_id:
            await websocket.send_json({"type": "error", "message": "Session ID required"})
            await websocket.close()
            return
        
        from db.models import Session as DBSession
        session = db.query(DBSession).filter(
            DBSession.session_id == session_id,
            DBSession.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if not session:
            await websocket.send_json({"type": "error", "message": "Invalid session"})
            await websocket.close()
            return
        
        user_id = session.user_id
        await manager.connect(user_id, websocket)
        
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "message": "Connected to WebSocket"
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "typing":
                chat_id = data.get("chat_id")
                is_typing = data.get("is_typing", False)
                
                if chat_id:
                    set_typing_status(chat_id, user_id, is_typing)
                    
                    recipient_id = data.get("recipient_id")
                    if recipient_id:
                        await manager.send_personal_message({
                            "type": "typing",
                            "user_id": user_id,
                            "is_typing": is_typing,
                            "chat_id": chat_id
                        }, recipient_id)
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(user_id)
    except Exception as e:
        if user_id:
            manager.disconnect(user_id)
        print(f"WebSocket error: {e}")