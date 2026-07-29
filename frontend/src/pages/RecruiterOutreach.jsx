import React, { useState } from 'react';
import { Target, ExternalLink, Mail, Copy } from 'lucide-react';
import axios from 'axios';

const API_BASE = '/api';

export default function RecruiterOutreach({ token }) {
    const [recruiters, setRecruiters] = useState([]);
    const [draft, setDraft] = useState('');
    const [loading, setLoading] = useState(false);
    const [initialLoading, setInitialLoading] = useState(true);
    const [selectedAgency, setSelectedAgency] = useState(null);
    const [errorMsg, setErrorMsg] = useState(null);

    React.useEffect(() => {
        const fetchRecruiters = async () => {
            try {
                setInitialLoading(true);
                const res = await axios.get(`${API_BASE}/recruiters/list`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                const data = res.data.data || res.data;
                setRecruiters(Array.isArray(data) ? data : []);
            } catch (e) {
                console.error("Failed to load recruiters list", e);
            } finally {
                setInitialLoading(false);
            }
        };
        fetchRecruiters();
    }, [token]);

    const generateOutreach = async (agencyName) => {
        setLoading(true);
        setSelectedAgency(agencyName);
        setErrorMsg(null);
        setDraft('');
        try {
            const res = await axios.post(`${API_BASE}/recruiters/draft`, {
                agency: agencyName
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setDraft(res.data.reply);
        } catch (e) {
            console.error(e);
            if (e.response && e.response.data && e.response.data.detail) {
                setErrorMsg(e.response.data.detail);
            } else {
                setErrorMsg("Failed to generate outreach draft.");
            }
        } finally {
            setLoading(false);
        }
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        alert("Copied to clipboard!");
    };


    return (
        <div className="fade-in" style={{ padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Target size={24} style={{ color: 'var(--accent)' }}/> External Recruiter Outreach
            </h2>
            <p className="subtitle" style={{ marginBottom: '0.5rem' }}>
                Connect with specialized tech staffing agencies. Use the AI to generate a cold-outreach note, then click the LinkedIn button to manually find and message a recruiter at that agency.
            </p>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
                <em>Note: Free LinkedIn accounts are limited to roughly 5 personalized connection notes per month. Use them strategically!</em>
            </p>


            {errorMsg && (
                <div style={{ padding: '1rem 1.5rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '12px', marginBottom: '2rem', color: '#fca5a5' }}>
                    <strong>Warning:</strong> {errorMsg}
                </div>
            )}

            {draft && selectedAgency && !errorMsg && (
                <div style={{ padding: '1.5rem', background: 'rgba(79, 70, 229, 0.1)', border: '1px solid rgba(79, 70, 229, 0.3)', borderRadius: '12px', marginBottom: '2rem' }}>
                    <h3 style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Mail size={18} style={{ color: 'var(--accent)' }} /> Generated Draft for {selectedAgency}
                    </h3>
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', fontSize: '0.95rem', color: '#e2e8f0', whiteSpace: 'pre-wrap' }}>
                        {draft}
                    </div>
                    <button 
                        className="btn btn-secondary"
                        onClick={() => copyToClipboard(draft)}
                        style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '6px' }}
                    >
                        <Copy size={16} /> Copy Note
                    </button>
                </div>
            )}

            {initialLoading ? (
                <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-secondary)' }}>
                    <div className="spinner" style={{ margin: '0 auto 1rem auto' }}></div>
                    <p>AI is identifying top tech staffing agencies for your specific roles and locations...</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
                    {recruiters.map((agency, i) => (
                    <div key={i} className="premium-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div>
                            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.15rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                                <span>{agency.name}</span>
                                {agency.match_score && (
                                    <span style={{ fontSize: '0.8rem', background: 'var(--accent)', color: 'white', padding: '2px 8px', borderRadius: '12px', whiteSpace: 'nowrap' }}>
                                        {agency.match_score}% Match
                                    </span>
                                )}
                            </h3>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                                <span style={{ background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '4px', marginRight: '8px' }}>{agency.type}</span>
                                {agency.specialty}
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                                {agency.region && (
                                    <span style={{ fontSize: '0.75rem', background: 'rgba(79, 70, 229, 0.2)', color: '#a5b4fc', padding: '2px 6px', borderRadius: '4px' }}>
                                        📍 {agency.region}
                                    </span>
                                )}
                                {agency.domains && agency.domains.map(d => (
                                    <span key={d} style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.05)', color: '#cbd5e1', padding: '2px 6px', borderRadius: '4px' }}>
                                        {d.replace('_', '/').toUpperCase()}
                                    </span>
                                ))}
                                {agency.early_career && (
                                     <span style={{ fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.2)', color: '#6ee7b7', padding: '2px 6px', borderRadius: '4px' }}>
                                         Fresher-Friendly
                                     </span>
                                )}
                            </div>
                        </div>
                        
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginTop: 'auto' }}>
                            <button 
                                className="btn btn-secondary"
                                onClick={() => generateOutreach(agency.name)}
                                disabled={loading}
                                style={{ fontSize: '0.85rem', padding: '0.5rem', display: 'flex', justifyContent: 'center' }}
                            >
                                {loading && selectedAgency === agency.name ? 'Drafting...' : '1. Draft Note'}
                            </button>
                            <a 
                                href={`https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent("tech recruiter " + agency.name)}`}
                                target="_blank"
                                rel="noreferrer"
                                className="btn"
                                style={{ background: '#0a66c2', fontSize: '0.85rem', padding: '0.5rem', display: 'flex', justifyContent: 'center', gap: '6px' }}
                            >
                                <ExternalLink size={14} /> 2. Find on LinkedIn
                            </a>
                        </div>
                    </div>
                ))}
                </div>
            )}
        </div>
    );
}
