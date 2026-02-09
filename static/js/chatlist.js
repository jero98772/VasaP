const { useState } = React;

function ChatList() {
    const [searchTerm, setSearchTerm] = useState('');
    
    // Mock chat data
    const [chats, setChats] = useState([
        {
            id: 1,
            name: 'Neo',
            lastMessage: 'Follow the white rabbit...',
            timestamp: '2m',
            unread: 3,
            online: true,
            avatar: '🕴️'
        },
        {
            id: 2,
            name: 'Trinity',
            lastMessage: 'The Matrix has you',
            timestamp: '15m',
            unread: 0,
            online: true,
            avatar: '👩‍💻'
        },
        {
            id: 3,
            name: 'Morpheus',
            lastMessage: 'What is real?',
            timestamp: '1h',
            unread: 1,
            online: false,
            avatar: '🕶️'
        },
        {
            id: 4,
            name: 'Agent Smith',
            lastMessage: 'Mr. Anderson...',
            timestamp: '3h',
            unread: 0,
            online: false,
            avatar: '🤵'
        },
        {
            id: 5,
            name: 'Oracle',
            lastMessage: 'I\'d ask you to sit down, but...',
            timestamp: '1d',
            unread: 0,
            online: true,
            avatar: '🔮'
        },
        {
            id: 6,
            name: 'Cypher',
            lastMessage: 'Ignorance is bliss',
            timestamp: '2d',
            unread: 0,
            online: false,
            avatar: '🐍'
        },
        {
            id: 7,
            name: 'Tank',
            lastMessage: 'I\'m going to learn Kung Fu',
            timestamp: '3d',
            unread: 0,
            online: false,
            avatar: '⚡'
        },
        {
            id: 8,
            name: 'Mouse',
            lastMessage: 'The woman in the red dress',
            timestamp: '5d',
            unread: 0,
            online: false,
            avatar: '🖱️'
        }
    ]);

    const filteredChats = chats.filter(chat =>
        chat.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const openChat = (chatId) => {
        window.location.href = `/chat/id/${chatId}`;
    };

    return (
        <div className="chat-container">
            <div className="chat-header">
                <div className="header-brand">
                    <div className="brand-logo">V</div>
                    <div className="brand-name">VassApp</div>
                </div>
                <div className="chat-status">
                    <div className="status-indicator"></div>
                    <span>E2E</span>
                </div>
            </div>

            <div className="chat-list-search">
                <div className="search-wrapper">
                    <span className="search-icon">🔍</span>
                    <input
                        type="text"
                        className="search-input"
                        placeholder="Search..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="chat-list-container">
                {filteredChats.length === 0 ? (
                    <div className="no-chats">
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
                        <div style={{ color: 'var(--text-gray)' }}>No contacts found</div>
                    </div>
                ) : (
                    filteredChats.map(chat => (
                        <div 
                            key={chat.id} 
                            className="chat-item"
                            onClick={() => openChat(chat.id)}
                        >
                            <div className="chat-item-avatar">
                                {chat.avatar}
                                {chat.online && <div className="online-badge"></div>}
                            </div>
                            
                            <div className="chat-item-content">
                                <div className="chat-item-header">
                                    <div className="chat-item-name">{chat.name}</div>
                                    <div className="chat-item-time">{chat.timestamp}</div>
                                </div>
                                <div className="chat-item-message">
                                    {chat.lastMessage}
                                </div>
                            </div>
                            
                            {chat.unread > 0 && (
                                <div className="unread-badge">
                                    {chat.unread}
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

ReactDOM.render(<ChatList />, document.getElementById('root'));