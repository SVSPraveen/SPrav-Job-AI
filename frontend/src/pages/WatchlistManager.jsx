import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Eye, Plus, Trash2, ExternalLink, Clock, Briefcase, Zap } from 'lucide-react';
import CompanyTypeahead from '../CompanyTypeahead';

const API_BASE = '/api';

function WatchlistManager({ token }) {
    const [companies, setCompanies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newName, setNewName] = useState('');
    const [newUrl, setNewUrl] = useState('');
    const [adding, setAdding] = useState(false);
    const [error, setError] = useState('');
    const [removingName, setRemovingName] = useState(null);

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
        setError('');
        try {
            await axios.post(`${API_BASE}/watchlist`,
                { action: 'add', company: { name: newName.trim(), careers_url: newUrl.trim() } },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setNewName('');
            setNewUrl('');
            fetchWatchlist();
        } catch (e) {
            setError('Failed to add company: ' + (e.response?.data?.detail || e.message));
        } finally {
            setAdding(false);
        }
    };

    const removeCompany = async (name) => {
        setRemovingName(name);
        try {
            await axios.post(`${API_BASE}/watchlist`,
                { action: 'remove', name },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            fetchWatchlist();
        } catch (e) {
            setError('Failed to remove company.');
        } finally {
            setRemovingName(null);
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

    const canAdd = newName.trim() && newUrl.trim() && !adding;

    return (
        <div className="fade-in">

            {/* Page Header */}
            <div style={{ marginBottom: '2rem' }}>
                <h2 style={{ margin: '0 0 0.4rem 0', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <Eye size={22} style={{ color: 'var(--accent)' }} /> Career Page Watchlist
                </h2>
                <p className="subtitle" style={{ margin: 0 }}>
                    The AI polls these company career pages every 15 minutes. The moment a new role
                    appears — even a stealth posting — it enters the pipeline before anyone else sees it.
                </p>
            </div>

            {/* Add Company Card */}
            <div className="premium-card" style={{ marginBottom: '2rem' }}>
                <h3 style={{ margin: '0 0 1.25rem 0', fontSize: '0.8rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
                    Add a Company to Watch
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr auto', gap: '1rem', alignItems: 'flex-end' }}>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.4rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                            Company Name
                        </label>
                        <CompanyTypeahead
                            onAdd={(val) => setNewName(val)}
                            placeholder="e.g. Zepto, Swiggy…"
                        />
                        {newName && (
                            <div style={{ marginTop: '0.3rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                Selected: <strong style={{ color: 'var(--text-primary)' }}>{newName}</strong>
                                <button onClick={() => setNewName('')} style={{ marginLeft: '0.5rem', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.8rem' }}>✕ clear</button>
                            </div>
                        )}
                    </div>

                    <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.4rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                            Careers Page URL
                        </label>
                        <input
                            id="wl-careers-url"
                            className="input"
                            value={newUrl}
                            onChange={e => setNewUrl(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && canAdd && addCompany()}
                            placeholder="e.g. https://jobs.lever.co/zepto"
                            style={{ width: '100%', boxSizing: 'border-box' }}
                        />
                    </div>

                    <button
                        id="wl-add-btn"
                        className="btn"
                        onClick={addCompany}
                        disabled={!canAdd}
                        style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', whiteSpace: 'nowrap', alignSelf: 'flex-end' }}
                    >
                        <Plus size={15} /> {adding ? 'Adding…' : 'Add Company'}
                    </button>
                </div>

                {error && (
                    <p style={{ color: 'var(--error)', marginTop: '0.75rem', fontSize: '0.88rem', margin: '0.75rem 0 0' }}>{error}</p>
                )}
            </div>

            {/* Company List */}
            {loading ? (
                <div style={{ color: 'var(--text-secondary)', padding: '2rem 0', textAlign: 'center' }}>
                    Loading watchlist…
                </div>
            ) : companies.length === 0 ? (
                <div className="premium-card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
                    <Eye size={36} style={{ opacity: 0.25, marginBottom: '1rem' }} />
                    <p style={{ margin: 0, fontSize: '1rem' }}>No companies being watched yet.</p>
                    <p style={{ margin: '0.4rem 0 0', fontSize: '0.88rem' }}>Add one above to start monitoring for stealth postings.</p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                            {companies.length} compan{companies.length === 1 ? 'y' : 'ies'} monitored
                        </span>
                    </div>
                    {companies.map((company, idx) => (
                        <div
                            key={idx}
                            className="item-card"
                            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.25rem' }}
                        >
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem' }}>
                                    <strong style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>{company.name}</strong>
                                    <span style={{
                                        fontSize: '0.73rem',
                                        fontWeight: 600,
                                        padding: '2px 9px',
                                        borderRadius: '100px',
                                        background: company.job_count > 0 ? 'rgba(16,185,129,0.15)' : 'var(--bg-surface-hover)',
                                        color: company.job_count > 0 ? 'var(--success)' : 'var(--text-muted)',
                                        border: company.job_count > 0 ? '1px solid rgba(16,185,129,0.3)' : '1px solid var(--border-subtle)',
                                    }}>
                                        <Briefcase size={10} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '3px' }} />
                                        {company.job_count} job{company.job_count !== 1 ? 's' : ''} tracked
                                    </span>
                                </div>
                                <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.82rem', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                        <Clock size={12} /> Last checked: {formatDate(company.last_checked)}
                                    </span>
                                    <a
                                        href={company.careers_url}
                                        target="_blank"
                                        rel="noreferrer"
                                        style={{ color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: '0.25rem', textDecoration: 'none' }}
                                    >
                                        <ExternalLink size={12} /> Open careers page
                                    </a>
                                </div>
                            </div>
                            <button
                                onClick={() => removeCompany(company.name)}
                                disabled={removingName === company.name}
                                style={{
                                    marginLeft: '1.5rem',
                                    flexShrink: 0,
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.3rem',
                                    background: 'transparent',
                                    border: '1px solid rgba(239,68,68,0.35)',
                                    color: 'var(--error)',
                                    borderRadius: '8px',
                                    padding: '0.4rem 0.9rem',
                                    fontSize: '0.83rem',
                                    cursor: removingName === company.name ? 'not-allowed' : 'pointer',
                                    opacity: removingName === company.name ? 0.5 : 1,
                                    transition: 'all 0.2s',
                                }}
                                onMouseOver={e => e.currentTarget.style.background = 'rgba(239,68,68,0.08)'}
                                onMouseOut={e => e.currentTarget.style.background = 'transparent'}
                            >
                                <Trash2 size={13} /> {removingName === company.name ? 'Removing…' : 'Remove'}
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* How it works note */}
            <div className="premium-card" style={{ marginTop: '2rem', padding: '1rem 1.25rem', borderLeft: '3px solid var(--accent)', background: 'rgba(99,102,241,0.06)' }}>
                <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'flex-start', gap: '0.6rem' }}>
                    <Zap size={15} style={{ color: 'var(--accent)', flexShrink: 0, marginTop: '1px' }} />
                    <span>
                        <strong style={{ color: 'var(--text-primary)' }}>How it works: </strong>
                        On first run, the watcher saves a snapshot of each career page (baseline capture — no jobs injected).
                        On every subsequent poll, it diffs the live page against the snapshot. Any new listing — even
                        a stealth posting that closes in minutes — is immediately scored, tailored, and queued for auto-apply.
                    </span>
                </p>
            </div>
        </div>
    );
}

export default WatchlistManager;
