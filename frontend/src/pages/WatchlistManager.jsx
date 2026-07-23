import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

function WatchlistManager({ token }) {
    const [companies, setCompanies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newName, setNewName] = useState('');
    const [newUrl, setNewUrl] = useState('');
    const [adding, setAdding] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (token) fetchWatchlist();
    }, [token]);

    const fetchWatchlist = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/watchlist`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setCompanies(res.data);
        } catch (e) {
            setError('Failed to load watchlist.');
        } finally {
            setLoading(false);
        }
    };

    const addCompany = async () => {
        if (!newName.trim() || !newUrl.trim()) return;
        setAdding(true);
        try {
            await axios.post(`${API_BASE}/watchlist`,
                { action: 'add', company: { name: newName.trim(), careers_url: newUrl.trim() } },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setNewName('');
            setNewUrl('');
            fetchWatchlist();
        } catch (e) {
            setError('Failed to add company.');
        } finally {
            setAdding(false);
        }
    };

    const removeCompany = async (name) => {
        try {
            await axios.post(`${API_BASE}/watchlist`,
                { action: 'remove', name },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            fetchWatchlist();
        } catch (e) {
            setError('Failed to remove company.');
        }
    };

    const formatDate = (iso) => {
        if (!iso || iso === 'Never') return 'Never';
        try {
            return new Date(iso).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' });
        } catch {
            return iso;
        }
    };

    return (
        <div className="fade-in">
            <div style={{ marginBottom: '2rem' }}>
                <h2 style={{ margin: '0 0 0.4rem 0' }}>Career Page Watchlist</h2>
                <p className="subtitle" style={{ margin: 0 }}>
                    The AI polls these company career pages every 15 minutes. The moment a new role appears — 
                    even a stealth posting — it enters the pipeline and gets auto-applied to before anyone else sees it.
                </p>
            </div>

            {/* Add Company Form */}
            <div className="glass-card" style={{ marginBottom: '2rem', padding: '1.5rem' }}>
                <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem', color: 'var(--text-secondary)' }}>
                    ADD A COMPANY TO WATCH
                </h3>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
                    <div style={{ flex: 1, minWidth: '200px' }}>
                        <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.4rem', color: 'var(--text-secondary)' }}>
                            Company Name
                        </label>
                        <input
                            id="wl-company-name"
                            className="input"
                            value={newName}
                            onChange={e => setNewName(e.target.value)}
                            placeholder="e.g. Zepto"
                        />
                    </div>
                    <div style={{ flex: 2, minWidth: '300px' }}>
                        <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.4rem', color: 'var(--text-secondary)' }}>
                            Careers Page URL
                        </label>
                        <input
                            id="wl-careers-url"
                            className="input"
                            value={newUrl}
                            onChange={e => setNewUrl(e.target.value)}
                            placeholder="e.g. https://jobs.lever.co/zepto"
                        />
                    </div>
                    <button
                        id="wl-add-btn"
                        className="btn"
                        onClick={addCompany}
                        disabled={adding || !newName.trim() || !newUrl.trim()}
                        style={{ flexShrink: 0 }}
                    >
                        {adding ? 'Adding...' : '+ Add'}
                    </button>
                </div>
                {error && <p style={{ color: 'var(--error)', marginTop: '0.5rem', fontSize: '0.9rem' }}>{error}</p>}
            </div>

            {/* Company List */}
            {loading ? (
                <p style={{ color: 'var(--text-secondary)' }}>Loading watchlist...</p>
            ) : companies.length === 0 ? (
                <p style={{ color: 'var(--text-secondary)' }}>No companies being watched yet. Add one above!</p>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {companies.map((company, idx) => (
                        <div
                            key={idx}
                            className="glass-card"
                            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.25rem' }}
                        >
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.3rem' }}>
                                    <strong style={{ fontSize: '1rem' }}>{company.name}</strong>
                                    <span
                                        style={{
                                            fontSize: '0.75rem',
                                            padding: '2px 8px',
                                            borderRadius: '100px',
                                            background: company.job_count > 0 ? 'var(--success)' : 'var(--surface)',
                                            color: company.job_count > 0 ? '#fff' : 'var(--text-secondary)',
                                        }}
                                    >
                                        {company.job_count} job{company.job_count !== 1 ? 's' : ''} tracked
                                    </span>
                                </div>
                                <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                                    <span>🕐 Last checked: {formatDate(company.last_checked)}</span>
                                    <a href={company.careers_url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)' }}>
                                        Open careers page ↗
                                    </a>
                                </div>
                            </div>
                            <button
                                className="btn"
                                onClick={() => removeCompany(company.name)}
                                style={{
                                    background: 'transparent',
                                    border: '1px solid var(--error)',
                                    color: 'var(--error)',
                                    padding: '0.4rem 1rem',
                                    fontSize: '0.85rem',
                                    flexShrink: 0,
                                }}
                            >
                                Remove
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Info note */}
            <div className="glass-card" style={{ marginTop: '2rem', padding: '1rem 1.25rem', borderLeft: '3px solid var(--accent)', background: 'rgba(99,102,241,0.07)' }}>
                <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                    <strong style={{ color: 'var(--text)' }}>How it works: </strong>
                    On first run, the watcher saves a snapshot of each career page and does not inject any jobs 
                    (baseline capture). On every subsequent run, it diffs the live page against the snapshot. 
                    Any new listing that appears — even a stealth posting that closes in minutes — is immediately 
                    injected into the AI pipeline, scored, tailored, and auto-applied to.
                </p>
            </div>
        </div>
    );
}

export default WatchlistManager;
