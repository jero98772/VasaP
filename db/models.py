from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship, validates
from datetime import datetime, timezone
from db.db import Base


class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(16), primary_key=True)
    encrypted_username = Column(Text, nullable=False)
    verification_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    last_seen = Column(DateTime(timezone=True), nullable=True)
    encryption_key_salt = Column(Text, nullable=False)
    
    # Relationships
    sent_messages = relationship(
        "Message", 
        back_populates="sender", 
        foreign_keys="Message.sender_id"
    )
    received_messages = relationship(
        "Message", 
        back_populates="recipient", 
        foreign_keys="Message.recipient_id"
    )
    conversations_as_user = relationship(
        "Conversation",
        back_populates="user",
        foreign_keys="Conversation.user_id"
    )
    conversations_as_other = relationship(
        "Conversation",
        back_populates="other_user",
        foreign_keys="Conversation.other_user_id"
    )
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    @validates('user_id')
    def validate_user_id(self, key, user_id):
        if len(user_id) != 16:
            raise ValueError("user_id must be exactly 16 characters")
        return user_id


class Message(Base):
    __tablename__ = "messages"
    
    message_id = Column(String(16), primary_key=True)
    sender_id = Column(
        String(16),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    recipient_id = Column(
        String(16),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    encrypted_content = Column(Text, nullable=False)
    encrypted_metadata = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    read_status = Column(Boolean, nullable=False, default=False)
    thread_id = Column(String(16), nullable=True)
    
    # Relationships
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    recipient = relationship("User", back_populates="received_messages", foreign_keys=[recipient_id])
    
    __table_args__ = (
        Index('idx_conversation', 'sender_id', 'recipient_id', 'timestamp'),
        Index('idx_unread', 'recipient_id', 'read_status'),
        CheckConstraint("sender_id != recipient_id", name="check_different_users"),
    )
    
    @validates('message_id')
    def validate_message_id(self, key, message_id):
        if len(message_id) != 16:
            raise ValueError("message_id must be exactly 16 characters")
        return message_id
    
    @validates('encrypted_content')
    def validate_content(self, key, content):
        if not content or len(content.strip()) == 0:
            raise ValueError("Message content cannot be empty")
        return content


class Conversation(Base):
    __tablename__ = "conversations"
    
    user_id = Column(
        String(16),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    other_user_id = Column(
        String(16),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    last_message_id = Column(String(16), nullable=True)
    last_message_timestamp = Column(DateTime(timezone=True), nullable=True)
    unread_count = Column(Integer, nullable=False, default=0)
    encrypted_summary = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations_as_user", foreign_keys=[user_id])
    other_user = relationship("User", back_populates="conversations_as_other", foreign_keys=[other_user_id])
    
    __table_args__ = (
        Index('idx_recent', 'user_id', 'last_message_timestamp'),
        CheckConstraint("user_id != other_user_id", name="check_different_conversation_users"),
    )
    
    @validates('unread_count')
    def validate_unread_count(self, key, count):
        if count < 0:
            raise ValueError("Unread count cannot be negative")
        return count


class UserSession(Base):
    __tablename__ = "sessions"
    
    session_id = Column(String(32), primary_key=True)
    user_id = Column(
        String(16),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    encryption_key_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index('idx_expiry', 'expires_at'),
    )
    
    @validates('session_id')
    def validate_session_id(self, key, session_id):
        if len(session_id) != 32:
            raise ValueError("session_id must be exactly 32 characters")
        return session_id


class Config(Base):
    __tablename__ = "config"
    
    config_key = Column(String(50), primary_key=True)
    config_value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    @validates('config_key')
    def validate_config_key(self, key, config_key):
        if len(config_key) > 50:
            raise ValueError("config_key must be 50 characters or less")
        return config_key