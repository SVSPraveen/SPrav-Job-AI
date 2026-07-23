import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

function HumanApply({ token }) {
    const [jobs, setJobs] = useState([]);

    useEffect(() => {
        if (token) fetchJobs();
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

    return (
        <div className="fade-in">
            <h2>Human Apply Queue</h2>
            <p className="subtitle">Jobs prepared by SPrav that require you to manually click apply (LinkedIn, Naukri, Workday).</p>
            
            {jobs.length === 0 ? (
                <p style={{ color: 'var(--text-secondary)' }}>You are all caught up! No manual applications pending.</p>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {jobs.map(job => (
                        <div key={job.id} className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <h3 style={{ margin: '0 0 0.5rem 0' }}>{job.title} at {job.company}</h3>
                                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0 }}>
                                    Match: {job.fit_score} | <a href={job.url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)' }}>Go to Job Posting</a>
                                </p>
                            </div>
                            <button 
                                className="btn" 
                                style={{ background: 'var(--success)' }} 
                                onClick={() => markApplied(job.id)}
                            >
                                I Applied
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default HumanApply;
