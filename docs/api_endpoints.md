API Endpoints
Authentication Endpoints
text

POST   /auth/login           - Login with mnemonic phrase
POST   /auth/register        - Create new account
POST   /auth/logout          - Logout current session
GET    /auth/session         - Get current session info
GET    /auth/users           - List all users
GET    /auth/mnemomic        - Get current mnemomic user info
GET    /auth/users/:id       - Get specific user info

----

Message Endpoints
text

GET    /chat/conversations   - List all conversations
GET    /chat/conversations/:userId/messages - Get conversation thread
POST   /chat/messages        - Send new message
PUT    /chat/messages/:id/read - Mark message as read
GET    /chat/messages/unread - Count unread messages

WebSocket Endpoints
text

WS     /ws                  - Real-time messaging

