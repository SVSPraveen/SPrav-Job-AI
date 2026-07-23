import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

function Settings({ token }) {
    const [creds, setCreds] = useState({});
    const [linkedinEmail, setLinkedinEmail] = useState('');
    const [linkedinPassword, setLinkedinPassword] = useState('');
    const [naukriEmail, setNaukriEmail] = useState('');
    const [naukriPassword, setNaukriPassword] = useState('');
    const [saving, setSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState('');
    const [activeSave, setActiveSave] = useState('');

    useEffect(() => {
        if (token) fetchCredentials();
    }, [token]);

    const fetchCredentials = async () => {
        try {
            const res = await axios.get(`${API_BASE}/credentials`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setCreds(res.data);
        } catch (e) {
            console.error(e);
        }
    };

    const handleSaveLinkedin = async (e) => {
        e.preventDefault();
        setSaving(true); setSaveStatus(''); setActiveSave('linkedin');
        try {
            await axios.post(`${API_BASE}/credentials`, {
                service: 'linkedin',
                credentials: { email: linkedinEmail, password: linkedinPassword }
            }, { headers: { Authorization: `Bearer ${token}` } });
            setSaveStatus('Saved securely to local database.');
            setLinkedinEmail(''); setLinkedinPassword('');
            fetchCredentials();
        } catch (e) { setSaveStatus('Failed to save.'); } finally { setSaving(false); }
    };

    const handleSaveNaukri = async (e) => {
        e.preventDefault();
        setSaving(true); setSaveStatus(''); setActiveSave('naukri');
        try {
            await axios.post(`${API_BASE}/credentials`, {
                service: 'naukri',
                credentials: { email: naukriEmail, password: naukriPassword }
            }, { headers: { Authorization: `Bearer ${token}` } });
            setSaveStatus('Naukri credentials saved.');
            setNaukriEmail(''); setNaukriPassword('');
            fetchCredentials();
        } catch (e) { setSaveStatus('Failed to save.'); } finally { setSaving(false); }
    };

    const liStatus = creds['linkedin']?.['password']?.is_set ? '🟢 Configured' : '🔴 Not configured';

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <h1 style={{ fontSize: '1.8rem', marginBottom: '0.5rem' }}>Settings & Credentials</h1>
            <p className="subtitle" style={{ marginBottom: '2rem' }}>
                Manage your local account and application connections. 
                Everything here is stored securely on your machine.
            </p>

            <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem' }}>
                <h2 style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>
                    LinkedIn Scout
                </h2>
                
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                    <p style={{ margin: '0 0 0.5rem 0', color: 'var(--text-secondary)' }}>
                        <strong>Why is this needed?</strong> The headless browser needs to log in to read 
                        HR/CEO posts. Your credentials are encrypted and stored <strong>only on your local machine</strong>.
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem' }}>
                        <span>Current Status:</span> 
                        <strong style={{ color: creds['linkedin']?.['password']?.is_set ? 'var(--success)' : 'var(--error)' }}>
                            {liStatus}
                        </strong>
                    </div>
                </div>

                <form onSubmit={handleSaveLinkedin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '400px' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>LinkedIn Email</label>
                        <input 
                            type="email" 
                            className="input" 
                            style={{ width: '100%' }}
                            value={linkedinEmail}
                            onChange={e => setLinkedinEmail(e.target.value)}
                            placeholder={creds['linkedin']?.['email']?.is_set ? '••••••••' : 'Enter email'}
                            required
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>LinkedIn Password</label>
                        <input 
                            type="password" 
                            className="input" 
                            style={{ width: '100%' }}
                            value={linkedinPassword}
                            onChange={e => setLinkedinPassword(e.target.value)}
                            placeholder={creds['linkedin']?.['password']?.is_set ? '••••••••' : 'Enter password'}
                            required
                        />
                    </div>
                    <button type="submit" className="btn" disabled={saving || (!linkedinEmail && !linkedinPassword)}>
                        {saving ? 'Saving...' : 'Save Credentials'}
                    </button>
                    {saveStatus && <span style={{ fontSize: '0.85rem', color: 'var(--success)' }}>{saveStatus}</span>}
                </form>
            </div>

            <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem' }}>
                <h2 style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '1.3rem' }}>🇮🇳</span> Naukri.com Auto-Apply
                </h2>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                    <p style={{ margin: '0 0 0.5rem 0', color: 'var(--text-secondary)' }}>
                        <strong>Why is this needed?</strong> The Naukri Quick Apply bot logs into your Naukri
                        account and applies directly with one click. Credentials are encrypted and stored only on your machine.
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem' }}>
                        <span>Current Status:</span>
                        <strong style={{ color: creds['naukri']?.['password']?.is_set ? 'var(--success)' : 'var(--error)' }}>
                            {creds['naukri']?.['password']?.is_set ? '🟢 Configured' : '🔴 Not configured'}
                        </strong>
                    </div>
                </div>
                <form onSubmit={handleSaveNaukri} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '400px' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Naukri Email</label>
                        <input type="email" className="input" style={{ width: '100%' }} value={naukriEmail}
                            onChange={e => setNaukriEmail(e.target.value)}
                            placeholder={creds['naukri']?.['email']?.is_set ? '••••••••' : 'Enter Naukri email'} required />
                    </div>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Naukri Password</label>
                        <input type="password" className="input" style={{ width: '100%' }} value={naukriPassword}
                            onChange={e => setNaukriPassword(e.target.value)}
                            placeholder={creds['naukri']?.['password']?.is_set ? '••••••••' : 'Enter password'} required />
                    </div>
                    <button type="submit" className="btn" disabled={saving && activeSave === 'naukri'}>
                        {saving && activeSave === 'naukri' ? 'Saving...' : 'Save Naukri Credentials'}
                    </button>
                    {activeSave === 'naukri' && saveStatus && <span style={{ fontSize: '0.85rem', color: 'var(--success)' }}>{saveStatus}</span>}
                </form>
            </div>

            <div className="glass-card" style={{ padding: '2rem' }}>
                <h2 style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                    Gmail Integration
                </h2>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                    Gmail integration is currently configured via the <code>credentials.json</code> file in your project folder.
                    To re-authorize or change accounts, delete <code>token.json</code> and restart the application.
                </p>
            </div>
        </div>
    );
}

export default Settings;
