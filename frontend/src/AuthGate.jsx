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
            <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: 'var(--bg-base)' }}>
                <div className="loading-spinner"></div>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)' }}>
            <form onSubmit={handleSubmit} className="premium-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem', padding: '2.5rem', minWidth: '360px' }}>
                
                <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
                    <h2 style={{ margin: 0, fontSize: '1.75rem', color: 'var(--text-primary)', letterSpacing: '-0.025em' }}>
                        {mode === 'signup' ? 'Welcome to SPrav' : 'Welcome Back'}
                    </h2>
                    <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9375rem' }}>
                        {mode === 'signup' 
                            ? 'Create your local secure account to begin.' 
                            : 'Log in to your local account.'}
                    </p>
                </div>

                {error && (
                    <div style={{ padding: '0.875rem', backgroundColor: 'var(--danger-subtle)', borderLeft: '3px solid var(--danger)', color: '#f87171', fontSize: '0.875rem', borderRadius: '4px' }}>
                        {error}
                    </div>
                )}

                {mode === 'signup' && (
                    <div>
                        <label className="input-label">Full Name</label>
                        <input 
                            type="text" 
                            placeholder="John Doe" 
                            value={name} 
                            onChange={e => setName(e.target.value)} 
                            className="input-field"
                            required 
                        />
                    </div>
                )}
                
                <div>
                    <label className="input-label">Email Address</label>
                    <input 
                        type="email" 
                        placeholder="you@example.com" 
                        value={email} 
                        onChange={e => setEmail(e.target.value)} 
                        className="input-field"
                        required 
                    />
                </div>
                
                <div>
                    <label className="input-label">Password</label>
                    <input 
                        type="password" 
                        placeholder="••••••••" 
                        value={password} 
                        onChange={e => setPassword(e.target.value)} 
                        className="input-field"
                        required 
                        minLength={6}
                    />
                </div>
                
                <button 
                    type="submit" 
                    className="btn"
                    style={{ marginTop: '0.5rem', padding: '0.75rem', fontSize: '1rem' }}
                    disabled={loading}
                >
                    {loading ? 'Processing...' : (mode === 'signup' ? 'Create Account' : 'Log In')}
                </button>

                <div style={{ textAlign: 'center', marginTop: '0.5rem' }}>
                    <button 
                        type="button" 
                        onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
                        style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.875rem', fontWeight: '500' }}
                        onMouseOver={(e) => e.target.style.color = 'var(--text-primary)'}
                        onMouseOut={(e) => e.target.style.color = 'var(--text-secondary)'}
                    >
                        {mode === 'login' ? "Don't have an account? Sign up" : "Already have an account? Log in"}
                    </button>
                </div>
            </form>
        </div>
    );
}

export default AuthGate;
