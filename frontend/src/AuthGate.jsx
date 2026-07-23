import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './index.css';

const API_BASE = 'http://localhost:8000/api';

function AuthGate({ setToken }) {
    const [mode, setMode] = useState('loading'); // 'loading' | 'login' | 'signup'
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const checkSetup = async () => {
            try {
                const res = await axios.get(`${API_BASE}/setup-check`);
                if (res.data.has_account) {
                    setMode('login');
                } else {
                    setMode('signup');
                }
            } catch (err) {
                console.error("Setup check failed", err);
                setMode('login'); // fallback
            }
        };
        checkSetup();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const url = mode === 'signup' ? `${API_BASE}/signup` : `${API_BASE}/login`;
        const payload = mode === 'signup' 
            ? { name, email, password } 
            : { email, password };

        try {
            const response = await axios.post(url, payload);
            setToken(response.data.access_token);
        } catch (err) {
            setError(err.response?.data?.detail || 'An error occurred. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    if (mode === 'loading') {
        return (
            <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: '#0f1115' }}>
                <div className="loading-spinner"></div>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: '#0f1115', color: '#fff' }}>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem', padding: '2.5rem', backgroundColor: '#1a1d24', borderRadius: '12px', minWidth: '340px', boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }}>
                
                <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
                    <h2 style={{ margin: 0, fontSize: '1.8rem', color: '#fff' }}>
                        {mode === 'signup' ? 'Welcome to SPrav' : 'Welcome Back'}
                    </h2>
                    <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        {mode === 'signup' 
                            ? 'Create your local secure account to begin.' 
                            : 'Log in to your local account.'}
                    </p>
                </div>

                {error && (
                    <div style={{ padding: '0.8rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', borderLeft: '3px solid var(--error)', color: 'var(--error)', fontSize: '0.9rem', borderRadius: '4px' }}>
                        {error}
                    </div>
                )}

                {mode === 'signup' && (
                    <input 
                        type="text" 
                        placeholder="Full Name" 
                        value={name} 
                        onChange={e => setName(e.target.value)} 
                        className="input"
                        required 
                    />
                )}
                
                <input 
                    type="email" 
                    placeholder="Email Address" 
                    value={email} 
                    onChange={e => setEmail(e.target.value)} 
                    className="input"
                    required 
                />
                
                <input 
                    type="password" 
                    placeholder="Password" 
                    value={password} 
                    onChange={e => setPassword(e.target.value)} 
                    className="input"
                    required 
                    minLength={6}
                />
                
                <button 
                    type="submit" 
                    className="btn"
                    style={{ marginTop: '0.5rem', padding: '0.9rem', fontSize: '1rem' }}
                    disabled={loading}
                >
                    {loading ? 'Processing...' : (mode === 'signup' ? 'Create Account' : 'Log In')}
                </button>
            </form>
        </div>
    );
}

export default AuthGate;
