import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './index.css';

const API_BASE = 'http://localhost:8000/api';

function AuthGate({ setToken }) {
    const [mode, setMode] = useState('loading'); // 'loading' | 'login' | 'signup' | 'recovery'
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [name, setName] = useState('');
    const [recoveryKey, setRecoveryKey] = useState('');
    const [newRecoveryKey, setNewRecoveryKey] = useState(null);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');

    useEffect(() => {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);
    }, []);

    useEffect(() => {
        const checkSetup = async () => {
            try {
                const res = await axios.get(`${API_BASE}/setup-check`);
                setMode(prev => {
                    if (prev !== 'loading') return prev;
                    return res.data.has_account ? 'login' : 'signup';
                });
            } catch (err) {
                console.error("Setup check failed", err);
                setMode(prev => prev === 'loading' ? 'login' : prev); // fallback
            }
        };
        checkSetup();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (mode === 'signup' && password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        if (mode === 'recovery' && password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        setLoading(true);

        if (mode === 'recovery') {
            try {
                const res = await axios.post(`${API_BASE}/reset-password`, {
                    email, recovery_key: recoveryKey, new_password: password
                });
                setSuccessMsg(res.data.message);
                setMode('login');
                setPassword('');
                setConfirmPassword('');
                setRecoveryKey('');
            } catch (err) {
                setError(err.response?.data?.detail || 'An error occurred. Please try again.');
            } finally {
                setLoading(false);
            }
            return;
        }

        const url = mode === 'signup' ? `${API_BASE}/signup` : `${API_BASE}/login`;
        const payload = mode === 'signup' 
            ? { name, email, password } 
            : { email, password };

        try {
            const response = await axios.post(url, payload);
            
            if (mode === 'signup' && response.data.recovery_key) {
                setNewRecoveryKey(response.data.recovery_key);
                setToken(response.data.access_token);
            } else {
                setToken(response.data.access_token);
            }
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

    if (newRecoveryKey) {
        return (
            <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)' }}>
                <div className="premium-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem', padding: '2.5rem', maxWidth: '450px' }}>
                    <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
                        <h2 style={{ margin: 0, fontSize: '1.75rem', color: 'var(--text-primary)' }}>Master Recovery Key</h2>
                        <p style={{ margin: '1rem 0 0 0', color: '#f87171', fontSize: '0.9375rem', fontWeight: 'bold' }}>
                            CRITICAL: SPrav is 100% offline. There is NO "Forgot Password" email.
                        </p>
                        <p style={{ margin: '0.5rem 0 1rem 0', color: 'var(--text-secondary)', fontSize: '0.9375rem' }}>
                            Copy this Master Recovery Key and save it somewhere secure. This is your ONLY way to regain access if you forget your password.
                        </p>
                    </div>
                    
                    <div style={{ padding: '1.5rem', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: '6px', textAlign: 'center', letterSpacing: '2px', fontFamily: 'monospace', fontSize: '1.25rem', color: 'var(--accent)' }}>
                        {newRecoveryKey}
                    </div>

                    <button 
                        onClick={() => setNewRecoveryKey(null)}
                        className="btn"
                        style={{ marginTop: '1rem', padding: '0.75rem', fontSize: '1rem' }}
                    >
                        I have securely saved my key
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)' }}>
            <form onSubmit={handleSubmit} className="premium-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem', padding: '2.5rem', minWidth: '360px' }}>
                
                <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
                    <h2 style={{ margin: 0, fontSize: '1.75rem', color: 'var(--text-primary)', letterSpacing: '-0.025em' }}>
                        {mode === 'signup' ? 'Welcome to SPrav' : mode === 'recovery' ? 'Reset Password' : 'Welcome Back'}
                    </h2>
                    <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9375rem' }}>
                        {mode === 'signup' 
                            ? 'Create your local secure account to begin.' 
                            : mode === 'recovery' ? 'Enter your Master Recovery Key.' 
                            : 'Log in to your local account.'}
                    </p>
                </div>

                {successMsg && (
                    <div style={{ padding: '0.875rem', backgroundColor: 'rgba(52, 211, 153, 0.1)', borderLeft: '3px solid #34d399', color: '#34d399', fontSize: '0.875rem', borderRadius: '4px' }}>
                        {successMsg}
                    </div>
                )}

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
                            placeholder="Enter your full name here..." 
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
                        placeholder="Enter your email address..." 
                        value={email} 
                        onChange={e => setEmail(e.target.value)} 
                        className="input-field"
                        required 
                    />
                </div>
                
                {mode === 'recovery' && (
                    <div>
                        <label className="input-label">Master Recovery Key</label>
                        <input 
                            type="text" 
                            placeholder="SPRAV-XXXX-XXXX" 
                            value={recoveryKey} 
                            onChange={e => setRecoveryKey(e.target.value.toUpperCase())} 
                            className="input-field"
                            required 
                        />
                    </div>
                )}
                
                <div>
                    <label className="input-label">{mode === 'recovery' ? 'New Password' : 'Password'}</label>
                    <div style={{ position: 'relative' }}>
                        <input 
                            type={showPassword ? "text" : "password"} 
                            placeholder="Enter a secure password..." 
                            value={password} 
                            onChange={e => setPassword(e.target.value)} 
                            className="input-field"
                            required 
                            minLength={6}
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1rem', color: 'var(--text-secondary)', padding: 0 }}
                            title={showPassword ? "Hide Password" : "Show Password"}
                        >
                            {showPassword ? '👁️' : '👁️‍🗨️'}
                        </button>
                    </div>
                </div>

                {mode === 'signup' || mode === 'recovery' ? (
                    <div>
                        <label className="input-label">Confirm Password</label>
                        <div style={{ position: 'relative' }}>
                            <input 
                                type={showPassword ? "text" : "password"} 
                                placeholder="Retype your password..." 
                                value={confirmPassword} 
                                onChange={e => setConfirmPassword(e.target.value)}
                                onPaste={e => e.preventDefault()} 
                                className="input-field"
                                required={mode === 'signup' || mode === 'recovery'} 
                                minLength={6}
                            />
                        </div>
                    </div>
                ) : null}
                
                <button 
                    type="submit" 
                    className="btn"
                    style={{ marginTop: '0.5rem', padding: '0.75rem', fontSize: '1rem' }}
                    disabled={loading}
                >
                    {loading ? 'Processing...' : (mode === 'signup' ? 'Create Account' : mode === 'recovery' ? 'Reset Password' : 'Log In')}
                </button>

                <div style={{ textAlign: 'center', marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <button 
                        type="button" 
                        onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setSuccessMsg(''); setError(''); }}
                        style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.875rem', fontWeight: '500' }}
                        onMouseOver={(e) => e.target.style.color = 'var(--text-primary)'}
                        onMouseOut={(e) => e.target.style.color = 'var(--text-secondary)'}
                    >
                        {mode === 'login' ? "Don't have an account? Sign up" : "Already have an account? Log in"}
                    </button>
                    {mode === 'login' && (
                        <button 
                            type="button" 
                            onClick={() => { setMode('recovery'); setError(''); }}
                            style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.875rem' }}
                            onMouseOver={(e) => e.target.style.color = 'var(--accent)'}
                            onMouseOut={(e) => e.target.style.color = 'var(--text-secondary)'}
                        >
                            Forgot Password?
                        </button>
                    )}
                </div>
            </form>
        </div>
    );
}

export default AuthGate;
