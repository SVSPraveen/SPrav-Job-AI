import React, { useState } from 'react';
import './index.css';

function Login({ setToken }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('http://localhost:8000/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            if (response.ok) {
                const data = await response.json();
                setToken(data.access_token);
            } else {
                setError('Invalid credentials');
            }
        } catch (err) {
            setError('Failed to connect to server');
        }
    };

    return (
        <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: '#111', color: '#fff' }}>
            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '2rem', backgroundColor: '#222', borderRadius: '8px', minWidth: '300px' }}>
                <h2 style={{ margin: 0, textAlign: 'center' }}>SPrav Login</h2>
                {error && <p style={{ color: 'red', margin: 0, textAlign: 'center' }}>{error}</p>}
                <input 
                    type="email" 
                    placeholder="Email" 
                    value={email} 
                    onChange={e => setEmail(e.target.value)} 
                    style={{ padding: '0.8rem', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#333', color: '#fff' }}
                    required 
                />
                <input 
                    type="password" 
                    placeholder="Password" 
                    value={password} 
                    onChange={e => setPassword(e.target.value)} 
                    style={{ padding: '0.8rem', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#333', color: '#fff' }}
                    required 
                />
                <button type="submit" style={{ padding: '0.8rem', borderRadius: '4px', border: 'none', backgroundColor: '#007BFF', color: '#fff', cursor: 'pointer', fontWeight: 'bold' }}>
                    Login
                </button>
            </form>
        </div>
    );
}

export default Login;
