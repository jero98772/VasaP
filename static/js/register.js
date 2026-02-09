const { useState } = React;

function Register() {
    const [username, setUsername] = useState('');
    const [mnemonic, setMnemonic] = useState('');
    const [showMnemonic, setShowMnemonic] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [copied, setCopied] = useState(false);

    const handleUsernameChange = (e) => {
        setUsername(e.target.value);
        setError('');
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/auth/mnemonic_register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username: username.trim() })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }

            setMnemonic(data.mnemonic);
            setShowMnemonic(true);
        } catch (err) {
            setError(err.message || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleCopyMnemonic = () => {
        navigator.clipboard.writeText(mnemonic).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        });
    };

    const handleContinueToLogin = () => {
        window.location.href = '/login';
    };

    if (showMnemonic) {
        return (
            <div className="container">
                <div className="auth-container">
                    <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                        <div className="logo" style={{ fontSize: '2.5rem' }}>SECURE CHAT</div>
                    </div>

                    <div className="form-card">
                        <div className="form-header">
                            <h2 className="form-title">// ACCOUNT CREATED //</h2>
                            <p className="form-subtitle" style={{ color: '#ff6b6b', marginBottom: '1rem' }}>
                                ⚠️ SAVE YOUR MNEMONIC PHRASE
                            </p>
                            <p className="form-subtitle">
                                This is the ONLY way to access your account. Store it securely!
                            </p>
                        </div>

                        <div style={{
                            background: 'var(--bg-black)',
                            border: '2px solid var(--neon-green)',
                            borderRadius: '8px',
                            padding: '1.5rem',
                            marginBottom: '1.5rem',
                            boxShadow: '0 0 20px var(--shadow-green)'
                        }}>
                            <div style={{
                                fontFamily: 'Share Tech Mono, monospace',
                                fontSize: '1.1rem',
                                lineHeight: '1.8',
                                color: 'var(--neon-green)',
                                wordBreak: 'break-word',
                                marginBottom: '1rem'
                            }}>
                                {mnemonic}
                            </div>
                            <button
                                onClick={handleCopyMnemonic}
                                className="btn"
                                style={{ width: '100%' }}
                            >
                                {copied ? '✓ COPIED!' : '📋 COPY TO CLIPBOARD'}
                            </button>
                        </div>

                        <div style={{
                            background: 'rgba(255, 107, 107, 0.1)',
                            border: '1px solid rgba(255, 107, 107, 0.3)',
                            borderRadius: '4px',
                            padding: '1rem',
                            marginBottom: '1.5rem'
                        }}>
                            <p style={{ color: '#ff6b6b', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                                <strong>IMPORTANT:</strong>
                            </p>
                            <ul style={{ color: 'var(--text-gray)', fontSize: '0.85rem', paddingLeft: '1.5rem', margin: 0 }}>
                                <li>Write this down on paper</li>
                                <li>Store it in a password manager</li>
                                <li>Never share it with anyone</li>
                                <li>We cannot recover your account if you lose this</li>
                            </ul>
                        </div>

                        <button
                            onClick={handleContinueToLogin}
                            className="btn"
                            style={{ width: '100%' }}
                        >
                            CONTINUE TO LOGIN
                        </button>
                    </div>

                    <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                        <a href="/" className="btn btn-secondary">← BACK TO HOME</a>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="container">
            <div className="auth-container">
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <div className="logo" style={{ fontSize: '2.5rem' }}>SECURE CHAT</div>
                </div>

                <div className="form-card">
                    <div className="form-header">
                        <h2 className="form-title">// CREATE ACCOUNT //</h2>
                        <p className="form-subtitle">
                            Register for encrypted communication
                        </p>
                    </div>

                    <form onSubmit={handleRegister}>
                        <div className="form-group">
                            <label className="form-label" htmlFor="username">USERNAME</label>
                            <input
                                type="text"
                                id="username"
                                name="username"
                                className="form-input"
                                placeholder="enter_username"
                                value={username}
                                onChange={handleUsernameChange}
                                required
                                minLength="3"
                                maxLength="50"
                            />
                            <small style={{ color: 'var(--text-gray)', fontSize: '0.85rem' }}>
                                3-50 characters, letters, numbers, underscores, and hyphens
                            </small>
                        </div>

                        <div style={{
                            background: 'rgba(0, 255, 65, 0.05)',
                            border: '1px solid rgba(0, 255, 65, 0.2)',
                            borderRadius: '4px',
                            padding: '1rem',
                            marginBottom: '1rem'
                        }}>
                            <p style={{ color: 'var(--neon-green)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                                <strong>🔐 How it works:</strong>
                            </p>
                            <ul style={{ color: 'var(--text-gray)', fontSize: '0.85rem', paddingLeft: '1.5rem', margin: 0 }}>
                                <li>No password needed</li>
                                <li>You'll receive a 12-word mnemonic phrase</li>
                                <li>This phrase is your ONLY way to login</li>
                                <li>Keep it safe - we cannot recover it</li>
                            </ul>
                        </div>

                        {error && (
                            <div style={{
                                padding: '12px',
                                background: 'rgba(255, 0, 0, 0.1)',
                                border: '1px solid rgba(255, 0, 0, 0.3)',
                                borderRadius: '4px',
                                color: '#ff4444',
                                marginBottom: '1rem',
                                fontSize: '0.9rem'
                            }}>
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            className="btn"
                            style={{ width: '100%', marginTop: '1rem' }}
                            disabled={loading}
                        >
                            {loading ? 'CREATING ACCOUNT...' : 'REGISTER'}
                        </button>
                    </form>

                    <div className="form-footer">
                        <p>
                            Already have an account?{' '}
                            <a href="/login" className="form-link">
                                Login here
                            </a>
                        </p>
                    </div>
                </div>

                <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                    <a href="/" className="btn btn-secondary">← BACK TO HOME</a>
                </div>
            </div>
        </div>
    );
}

ReactDOM.render(<Register />, document.getElementById('root'));