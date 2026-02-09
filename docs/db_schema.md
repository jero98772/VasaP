Database Schema
Users Table
text

users:
  user_id VARCHAR(16) PRIMARY KEY
  encrypted_username TEXT
  verification_hash TEXT
  created_at TIMESTAMP
  last_seen TIMESTAMP
  encryption_key_salt TEXT

Messages Table
text

messages:
  message_id VARCHAR(16) PRIMARY KEY
  sender_id VARCHAR(16) FOREIGN KEY (users.user_id)
  recipient_id VARCHAR(16) FOREIGN KEY (users.user_id)
  encrypted_content TEXT
  encrypted_metadata TEXT
  timestamp TIMESTAMP
  read_status BOOLEAN DEFAULT FALSE
  thread_id VARCHAR(16)
  
  INDEX idx_conversation (sender_id, recipient_id, timestamp)
  INDEX idx_unread (recipient_id, read_status)

Conversations Table (Denormalized for Performance)
text

conversations:
  user_id VARCHAR(16)
  other_user_id VARCHAR(16)
  last_message_id VARCHAR(16)
  last_message_timestamp TIMESTAMP
  unread_count INTEGER DEFAULT 0
  encrypted_summary TEXT
  
  PRIMARY KEY (user_id, other_user_id)
  INDEX idx_recent (user_id, last_message_timestamp DESC)

Session Storage
text

sessions:
  session_id VARCHAR(32) PRIMARY KEY
  user_id VARCHAR(16) FOREIGN KEY (users.user_id)
  encryption_key_hash TEXT
  created_at TIMESTAMP
  expires_at TIMESTAMP
  last_activity TIMESTAMP
  
  INDEX idx_expiry (expires_at)

App Configuration
text

config:
  config_key VARCHAR(50) PRIMARY KEY
  config_value TEXT
  updated_at TIMESTAMP