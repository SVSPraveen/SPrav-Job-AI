import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Briefcase, ExternalLink, Download, CheckCircle, Clock, Mail, Copy, ChevronDown, ChevronUp } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

function HumanApply({ token }) {
    const [jobs, setJobs] = useState([]);
    const [expandedEmails, setExpandedEmails] = useState({});

    useEffect(() => {
        if (token) fetchJobs();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token]);

    const fetchJobs = async () => {
        try {
            const res = await axios.get(`${API_BASE}/jobs/manual`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            // Filter to only show jobs waiting for human click
            setJobs(res.data.filter(j => j.status === 'pending_cover_letter' || j.status === 'manual_review'));
        } catch (e) {
            console.error(e);
        }
    };

    const markApplied = async (id) => {
        try {
            await axios.post(`${API_BASE}/jobs/${id}/apply`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            fetchJobs();
        } catch (e) {
            console.error(e);
        }
    };

    const toggleEmail = (id) => {
        setExpandedEmails(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        alert("Copied to clipboard!");
    };

    return (
        <div className="fade-in">
            <h2><CheckCircle size={22} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px' }} /> Action Required</h2>
            <p className="subtitle">Jobs prepared by SPrav that require you to manually apply or send a drafted email.</p>
            
            {jobs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '4rem 2rem', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.1)' }}>
                    <CheckCircle size={48} style={{ color: 'var(--success)', marginBottom: '1rem', opacity: 0.8 }} />
                    <h3 style={{ margin: '0 0 0.5rem 0' }}>You're all caught up!</h3>
                    <p style={{ color: 'var(--text-secondary)', margin: 0 }}>No manual applications pending in your queue.</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '1.5rem' }}>
                    {jobs.map(job => (
                        <div key={job.id} className="premium-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1.5rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <div>
                                    <h3 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.1rem' }}>
                                        <Briefcase size={16} style={{ color: 'var(--accent)' }} />
                                        {job.title}
                                    </h3>
                                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                                        {job.company}
                                    </div>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                            <div style={{width: '60px', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px'}}>
                                                <div style={{width: `${job.fit_score * 20}%`, height: '100%', background: 'var(--accent)', borderRadius: '2px'}}></div>
                                            </div>
                                            {job.fit_score}/5
                                        </span>
                                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                            <Clock size={12} /> Pending
                                        </span>
                                    </div>
                                </div>
                            </div>
                            
                            {job.url && job.url.includes('freshershunt') && (
                                <div style={{ display: 'inline-block', padding: '4px 8px', background: 'rgba(255, 107, 107, 0.1)', border: '1px solid rgba(255, 107, 107, 0.2)', borderRadius: '4px', color: '#ff6b6b', fontSize: '0.75rem', fontWeight: 600 }}>
                                    ⚡ Freshershunt Bypassed
                                </div>
                            )}

                            {job.strategy_report && (
                                <div style={{ marginTop: '0.5rem', background: 'rgba(79, 70, 229, 0.05)', border: '1px solid rgba(79, 70, 229, 0.2)', borderRadius: '8px', overflow: 'hidden' }}>
                                    <button 
                                        style={{ width: '100%', padding: '0.75rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer' }}
                                        onClick={() => toggleEmail(job.id)}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', fontWeight: 600 }}>
                                            <Mail size={16} style={{ color: 'var(--accent)' }} /> 
                                            Review Drafts & Strategy
                                        </div>
                                        {expandedEmails[job.id] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                    </button>
                                    
                                    {expandedEmails[job.id] && (
                                        <div style={{ padding: '0 1rem 1rem 1rem', borderTop: '1px solid rgba(79, 70, 229, 0.1)' }}>
                                            <div style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem', color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '4px', marginTop: '1rem' }}>
                                                {job.strategy_report}
                                            </div>
                                            <button 
                                                className="btn btn-secondary" 
                                                onClick={() => copyToClipboard(job.strategy_report)}
                                                style={{ width: '100%', marginTop: '0.75rem', display: 'flex', justifyContent: 'center', gap: '6px', fontSize: '0.85rem', padding: '0.5rem' }}
                                            >
                                                <Copy size={14} /> Copy to Clipboard
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                                <a 
                                    href={job.url} 
                                    target="_blank" 
                                    rel="noreferrer" 
                                    className="btn btn-secondary"
                                    style={{ padding: '0.6rem', fontSize: '0.85rem', display: 'flex', justifyContent: 'center', gap: '6px' }}
                                >
                                    <ExternalLink size={14} /> Open Portal
                                </a>
                                <a 
                                    href={`http://localhost:8000/resumes/${encodeURIComponent(job.company)}_Tailored.pdf`}
                                    download 
                                    target="_blank"
                                    rel="noreferrer"
                                    className="btn btn-secondary"
                                    style={{ padding: '0.6rem', fontSize: '0.85rem', display: 'flex', justifyContent: 'center', gap: '6px' }}
                                >
                                    <Download size={14} /> Resume
                                </a>
                            </div>
                            
                            <button 
                                className="btn" 
                                style={{ background: 'var(--success)', width: '100%', marginTop: '0.25rem', display: 'flex', justifyContent: 'center', gap: '6px', fontSize: '0.9rem', padding: '0.75rem' }} 
                                onClick={() => markApplied(job.id)}
                            >
                                <CheckCircle size={16} /> Mark as Applied
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default HumanApply;
