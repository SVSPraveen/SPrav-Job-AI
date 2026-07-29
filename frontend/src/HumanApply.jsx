import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Briefcase, ExternalLink, Download, CheckCircle, Clock, Mail, Copy, ChevronDown, ChevronUp, FileText, Star } from 'lucide-react';

const API_BASE = '/api';

function HumanApply({ token }) {
    const [jobs, setJobs] = useState([]);
    const [expandedIds, setExpandedIds] = useState({});

    useEffect(() => {
        if (token) fetchJobs();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token]);

    const fetchJobs = async () => {
        try {
            const res = await axios.get(`${API_BASE}/jobs/manual`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setJobs(res.data);
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

    const toggleExpand = (id) => {
        setExpandedIds(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const copyToClipboard = (text) => {
        if (!text) return;
        navigator.clipboard.writeText(text);
        alert("Copied to clipboard!");
    };

    const getAtsBadge = (url) => {
        const u = (url || "").toLowerCase();
        if (u.includes('myworkdayjobs') || u.includes('workday')) return { name: 'Workday', color: '#005CB9' };
        if (u.includes('icims.com')) return { name: 'iCIMS', color: '#D22630' };
        if (u.includes('smartrecruiters.com')) return { name: 'SmartRecruiters', color: '#00A3E0' };
        if (u.includes('naukri.com')) return { name: 'Naukri', color: '#275df5' };
        if (u.includes('wellfound.com')) return { name: 'Wellfound', color: '#E33F31' };
        return { name: 'Custom Portal', color: '#6b7280' };
    };

    return (
        <div className="fade-in">
            <h2><CheckCircle size={22} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px' }} /> Manual Apply Queue</h2>
            <p className="subtitle">Jobs on portals that block automation (Workday, iCIMS, Naukri) require a quick manual submission. Your tailored resume and screening answers are pre-drafted below.</p>
            
            {jobs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '4rem 2rem', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.1)' }}>
                    <CheckCircle size={48} style={{ color: 'var(--success)', marginBottom: '1rem', opacity: 0.8 }} />
                    <h3 style={{ margin: '0 0 0.5rem 0' }}>You're all caught up!</h3>
                    <p style={{ color: 'var(--text-secondary)', margin: 0 }}>No manual applications pending in your queue.</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '1.5rem' }}>
                    {jobs.map(job => {
                        const ats = getAtsBadge(job.url);
                        return (
                            <div key={job.id} className="premium-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1.5rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <div>
                                        <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                                            <span style={{ background: ats.color, color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold' }}>
                                                {ats.name}
                                            </span>
                                        </div>
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
                                                {job.fit_score}/5 Fit
                                            </span>
                                            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                <Clock size={12} /> Pending
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                
                                {ats.name === 'Workday' && (
                                    <div style={{ padding: '8px 12px', background: 'rgba(0, 92, 185, 0.1)', borderLeft: '3px solid #005CB9', borderRadius: '0 4px 4px 0', fontSize: '0.8rem', color: '#93c5fd' }}>
                                        <strong>Workday Notice:</strong> You must create a new account for this specific company tenant. Use your standard password alias.
                                    </div>
                                )}
                                {ats.name === 'iCIMS' && (
                                    <div style={{ padding: '8px 12px', background: 'rgba(210, 38, 48, 0.1)', borderLeft: '3px solid #D22630', borderRadius: '0 4px 4px 0', fontSize: '0.8rem', color: '#fca5a5' }}>
                                        <strong>iCIMS Notice:</strong> iCIMS job URLs expire extremely quickly. If the portal redirects to a search page, mark this job as "Closed/Redirected" - do not attempt to find it.
                                    </div>
                                )}
                                {ats.name === 'SmartRecruiters' && (
                                    <div style={{ padding: '8px 12px', background: 'rgba(0, 163, 224, 0.1)', borderLeft: '3px solid #00A3E0', borderRadius: '0 4px 4px 0', fontSize: '0.8rem', color: '#7dd3fc' }}>
                                        <strong>SmartRecruiters:</strong> One-click apply is usually supported if you log in. Attach the tailored resume below.
                                    </div>
                                )}
                                {ats.name === 'Naukri' && (
                                    <div style={{ padding: '8px 12px', background: 'rgba(39, 93, 245, 0.1)', borderLeft: '3px solid #275df5', borderRadius: '0 4px 4px 0', fontSize: '0.8rem', color: '#93c5fd' }}>
                                        <strong>Naukri Notice:</strong> Update your profile headline temporarily to match this role's target keywords before clicking apply.
                                    </div>
                                )}
                                
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginTop: '0.5rem' }}>
                                    <a 
                                        href={job.url} 
                                        target="_blank" 
                                        rel="noreferrer" 
                                        className="btn btn-secondary"
                                        style={{ padding: '0.6rem', fontSize: '0.85rem', display: 'flex', justifyContent: 'center', gap: '6px' }}
                                    >
                                        <ExternalLink size={14} /> 1. Open Portal
                                    </a>
                                    <a 
                                        href={`${API_BASE}/jobs/${job.id}/resume`}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="btn btn-secondary"
                                        style={{ padding: '0.6rem', fontSize: '0.85rem', display: 'flex', justifyContent: 'center', gap: '6px' }}
                                    >
                                        <Download size={14} /> 2. Download Resume
                                    </a>
                                </div>

                                <div style={{ marginTop: '0.5rem', background: 'rgba(79, 70, 229, 0.05)', border: '1px solid rgba(79, 70, 229, 0.2)', borderRadius: '8px', overflow: 'hidden' }}>
                                    <button 
                                        style={{ width: '100%', padding: '0.75rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer' }}
                                        onClick={() => toggleExpand(job.id)}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', fontWeight: 600 }}>
                                            <FileText size={16} style={{ color: 'var(--accent)' }} /> 
                                            3. Screening Answers & Stories
                                        </div>
                                        {expandedIds[job.id] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                    </button>
                                    
                                    {expandedIds[job.id] && (
                                        <div style={{ padding: '0 1rem 1rem 1rem', borderTop: '1px solid rgba(79, 70, 229, 0.1)' }}>
                                            <div style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem', color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '4px', marginTop: '1rem', maxHeight: '300px', overflowY: 'auto' }}>
                                                {job.evaluation_rubric && (
                                                    <>
                                                        <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-primary)' }}>Tailored Pitch / Cover Letter:</h4>
                                                        {job.evaluation_rubric}
                                                        <hr style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '1rem 0' }}/>
                                                    </>
                                                )}
                                                {job.star_stories && (
                                                    <>
                                                        <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-primary)' }}><Star size={12} style={{display:'inline'}}/> STAR Stories:</h4>
                                                        {job.star_stories}
                                                    </>
                                                )}
                                                {!job.evaluation_rubric && !job.star_stories && "No screening answers generated for this job."}
                                            </div>
                                            <button 
                                                className="btn btn-secondary" 
                                                onClick={() => copyToClipboard(job.evaluation_rubric || job.star_stories)}
                                                style={{ width: '100%', marginTop: '0.75rem', display: 'flex', justifyContent: 'center', gap: '6px', fontSize: '0.85rem', padding: '0.5rem' }}
                                            >
                                                <Copy size={14} /> Copy All
                                            </button>
                                        </div>
                                    )}
                                </div>
                                
                                <button 
                                    className="btn" 
                                    style={{ background: 'var(--success)', width: '100%', marginTop: 'auto', display: 'flex', justifyContent: 'center', gap: '6px', fontSize: '0.9rem', padding: '0.75rem' }} 
                                    onClick={() => markApplied(job.id)}
                                >
                                    <CheckCircle size={16} /> Mark as Applied
                                </button>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

export default HumanApply;
