from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv() 

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL","postgresql://user:password@localhost/messaging_db")

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_recycle=300, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def set_user_online(user_id: str):
    key = f"online:user:{user_id}"
    redis_client.setex(key, 300, "online")

def set_user_offline(user_id: str):
    key = f"online:user:{user_id}"
    redis_client.delete(key)

def is_user_online(user_id: str) -> bool:
    key = f"online:user:{user_id}"
    return redis_client.exists(key) == 1

def set_typing_status(chat_id: str, user_id: str, is_typing: bool):
    key = f"typing:chat:{chat_id}"
    if is_typing:
        redis_client.hset(key, user_id, "typing")
        redis_client.expire(key, 10)
    else:
        redis_client.hdel(key, user_id)

def get_typing_users(chat_id: str) -> list:
    key = f"typing:chat:{chat_id}"
    return list(redis_client.hkeys(key))

def add_message_to_queue(user_id: str, message_data: dict):
    key = f"queue:messages:{user_id}"
    redis_client.rpush(key, str(message_data))

def get_queued_messages(user_id: str) -> list:
    key = f"queue:messages:{user_id}"
    messages = redis_client.lrange(key, 0, -1)
    redis_client.delete(key)
    return messages