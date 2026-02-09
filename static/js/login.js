const { useState } = React;

function Login() {
    const [mnemonic, setMnemonic] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleInputChange = (e) => {
        setMnemonic(e.target.value);
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/auth/mnemonic_login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ mnemonic: mnemonic.trim() })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }

            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('username', data.username);
            localStorage.setItem('session_id', data.session_id);

            window.location.href = '/chat';
        } catch (err) {
            setError(err.message || 'Login failed. Please check your mnemonic and try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container">
            <div className="auth-container">
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <div className="logo" style={{ fontSize: '2.5rem' }}>SECURE CHAT</div>
                </div>

                <div className="form-card">
                    <div className="form-header">
                        <h2 className="form-title">// ACCESS TERMINAL //</h2>
                        <p className="form-subtitle">
                            Enter your 12-word mnemonic phrase to access secure chat
                        </p>
                    </div>

                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label className="form-label" htmlFor="mnemonic">MNEMONIC PHRASE</label>
                            <textarea
                                id="mnemonic"
                                name="mnemonic"
                                className="form-input"
                                placeholder="word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12"
                                value={mnemonic}
                                onChange={handleInputChange}
                                required
                                rows="3"
                                style={{ resize: 'none' }}
                            />
                            <small style={{ color: 'var(--text-gray)', fontSize: '0.85rem' }}>
                                Enter all 12 words separated by spaces
                            </small>
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
                            {loading ? 'LOGGING IN...' : 'LOGIN'}
                        </button>
                    </form>

                    <div className="form-footer">
                        <p>
                            Don't have an account?{' '}
                            <a href="/auth/register" className="form-link">
                                Register here
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

ReactDOM.render(<Login />, document.getElementById('root'));