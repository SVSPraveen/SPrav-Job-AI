import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Search } from 'lucide-react';

export default function JobDetailsModal({ jobId, onClose, token }) {
    const [jobDetails, setJobDetails] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDetails = async () => {
            try {
                // If in production or dev, the proxy might handle /api, but we'll use the relative path matching App.jsx
                const res = await axios.get(`/api/jobs/${jobId}/details`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setJobDetails(res.data);
            } catch (e) {
                console.error("Failed to fetch job details", e);
            } finally {
                setLoading(false);
            }
        };
        fetchDetails();
    }, [jobId, token]);

    const overlayStyle = {
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 9999,
        backdropFilter: 'blur(4px)'
    };

    const contentStyle = {
        backgroundColor: 'var(--bg-card)',
        padding: '2rem',
        borderRadius: '12px',
        maxWidth: '800px',
        width: '90%',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
        border: '1px solid rgba(255,255,255,0.05)'
    };

    if (loading) {
        return (
            <div style={overlayStyle}>
                <div style={contentStyle} className="loading-spinner"></div>
            </div>
        );
    }

    if (!jobDetails) {
        return (
            <div style={overlayStyle} onClick={onClose}>
                <div style={contentStyle} onClick={e => e.stopPropagation()}>
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <button className="btn" onClick={onClose} style={{ padding: '0.5rem', background: 'transparent' }}><X size={20}/></button>
                    </div>
                    <p style={{ color: '#fca5a5', textAlign: 'center' }}>Failed to load job details.</p>
                </div>
            </div>
        );
    }

    return (
        <div style={overlayStyle} onClick={onClose}>
            <div style={contentStyle} onClick={e => e.stopPropagation()}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
                    <h2 style={{ margin: 0, fontSize: '1.5rem' }}>{jobDetails.company} - {jobDetails.title}</h2>
                    <button className="btn" onClick={onClose} style={{ padding: '0.5rem', background: 'rgba(255,255,255,0.1)', border: 'none' }}><X size={20}/></button>
                </div>
                
                <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ marginBottom: '0.75rem', color: 'var(--accent)', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        🛡️ Auto-Apply Audit Log
                    </h3>
                    {jobDetails.audit ? (
                        <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                            <p style={{ margin: '0 0 0.5rem 0' }}><strong>Status:</strong> <span className={`badge ${jobDetails.audit.status}`}>{jobDetails.audit.status}</span></p>
                            <p style={{ margin: '0 0 0.5rem 0' }}><strong>Attempted At:</strong> {new Date(jobDetails.audit.attempted_at).toLocaleString()}</p>
                            <p style={{ margin: '0' }}><strong>Resume Hash (PDF Version):</strong> <code style={{ color: '#fbbf24', background: 'rgba(251, 191, 36, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>{jobDetails.audit.resume_version}</code></p>
                        </div>
                    ) : (
                        <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', border: '1px dashed rgba(255,255,255,0.1)' }}>
                            <p style={{ color: 'var(--text-secondary)', margin: 0 }}>No auto-apply audit record found for this job. It may be queued or required human review.</p>
                        </div>
                    )}
                </div>

                <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ marginBottom: '0.75rem', color: 'var(--accent)', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        🧠 AI Evaluation Rubric (Internal Logic)
                    </h3>
                    {jobDetails.evaluation_rubric ? (
                        <pre style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.85rem', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.05)' }}>
                            {jobDetails.evaluation_rubric}
                        </pre>
                    ) : (
                        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>No logic trace found. The job might not have reached the evaluation phase yet.</p>
                    )}
                </div>
                
                <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ marginBottom: '0.75rem', color: 'var(--accent)', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        ⚠️ Missing Skills Detected
                    </h3>
                    {jobDetails.missing_skills ? (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {jobDetails.missing_skills.split(',').map((skill, i) => (
                                <span key={i} style={{background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', padding: '4px 10px', borderRadius: '6px', fontSize: '0.85rem', border: '1px solid rgba(239, 68, 68, 0.3)'}}>
                                    {skill.trim()}
                                </span>
                            ))}
                        </div>
                    ) : (
                        <span style={{color: 'var(--text-secondary)'}}>No missing skills detected. Perfect match!</span>
                    )}
                </div>

                <div>
                    <h3 style={{ marginBottom: '0.75rem', color: 'var(--accent)', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        📄 Raw Job Description
                    </h3>
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', maxHeight: '300px', overflowY: 'auto', fontSize: '0.85rem', lineHeight: '1.6', color: '#cbd5e1', border: '1px solid rgba(255,255,255,0.05)' }}>
                        {jobDetails.description ? jobDetails.description.split('\n').map((line, i) => <p key={i} style={{ margin: '0 0 0.5rem 0' }}>{line}</p>) : 'No description extracted.'}
                    </div>
                </div>

            </div>
        </div>
    );
}
