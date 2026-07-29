import React, { useState } from 'react';
import axios from 'axios';
import { Target, BookOpen, MessageSquare, DollarSign, Loader2 } from 'lucide-react';

export default function InterviewPrepAssist({ jobDetails, token }) {
    const [offerSalary, setOfferSalary] = useState('');
    const [targetSalary, setTargetSalary] = useState('');
    const [competing, setCompeting] = useState('None');
    const [discount, setDiscount] = useState('Standard (no discount)');
    const [draft, setDraft] = useState('');
    const [loading, setLoading] = useState(false);

    if (!jobDetails || jobDetails.outcome !== 'interview') return null;

    const generateNegotiation = async () => {
        setLoading(true);
        try {
            const res = await axios.post('/api/action/negotiate', {
                company: jobDetails.company,
                role: jobDetails.title,
                offer_salary: offerSalary || 'Unknown',
                target_salary: targetSalary || 'Unknown',
                competing: competing,
                discount: discount
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setDraft(res.data.draft);
        } catch (e) {
            console.error(e);
            alert("Failed to generate negotiation script.");
        } finally {
            setLoading(false);
        }
    };

    let stories = [];
    try {
        stories = typeof jobDetails.star_stories === 'string' ? JSON.parse(jobDetails.star_stories) : (jobDetails.star_stories || []);
    } catch (e) {}

    return (
        <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '12px' }}>
            <h3 style={{ marginBottom: '1rem', color: '#10b981', fontSize: '1.3rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Target size={20} /> Interview & Offer Prep Center
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                {/* Left Column: STAR Stories & Tech Questions */}
                <div>
                    <h4 style={{ color: 'var(--text-primary)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <BookOpen size={16} style={{ color: '#3b82f6' }}/> Core STAR Stories
                    </h4>
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', maxHeight: '350px', overflowY: 'auto' }}>
                        {stories.length > 0 ? (
                            stories.map((s, i) => (
                                <div key={i} style={{ marginBottom: '1rem', paddingBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                    <strong style={{ color: '#60a5fa' }}>Situation:</strong> <span style={{ fontSize: '0.85rem' }}>{s.S || s.Situation}</span><br/>
                                    <strong style={{ color: '#f472b6' }}>Task:</strong> <span style={{ fontSize: '0.85rem' }}>{s.T || s.Task}</span><br/>
                                    <strong style={{ color: '#fbbf24' }}>Action:</strong> <span style={{ fontSize: '0.85rem' }}>{s.A || s.Action}</span><br/>
                                    <strong style={{ color: '#34d399' }}>Result:</strong> <span style={{ fontSize: '0.85rem' }}>{s.R || s.Result}</span>
                                </div>
                            ))
                        ) : (
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>No pre-generated STAR stories available for this job.</p>
                        )}
                        
                        {jobDetails.missing_skills && (
                            <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '6px' }}>
                                <strong style={{ color: '#fca5a5', fontSize: '0.9rem' }}>⚠️ Prepare to address these skill gaps:</strong>
                                <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.85rem', color: '#fecaca' }}>{jobDetails.missing_skills}</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Column: Negotiation AI */}
                <div>
                    <h4 style={{ color: 'var(--text-primary)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <DollarSign size={16} style={{ color: '#10b981' }}/> Offer Negotiation Copilot
                    </h4>
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Initial Offer ($)</label>
                                <input type="text" className="input" placeholder="e.g. 120k" value={offerSalary} onChange={e => setOfferSalary(e.target.value)} />
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Your Target ($)</label>
                                <input type="text" className="input" placeholder="e.g. 140k" value={targetSalary} onChange={e => setTargetSalary(e.target.value)} />
                            </div>
                        </div>
                        
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Competing Offers</label>
                            <input type="text" className="input" placeholder="e.g. Google offering 135k" value={competing} onChange={e => setCompeting(e.target.value)} />
                        </div>
                        
                        <button 
                            className="btn" 
                            style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '6px', background: 'var(--accent)' }}
                            onClick={generateNegotiation}
                            disabled={loading}
                        >
                            {loading ? <Loader2 size={16} className="spin" /> : <MessageSquare size={16} />}
                            Generate Negotiation Script
                        </button>
                        
                        {draft && (
                            draft.startsWith('ERROR:') ? (
                                <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', fontSize: '0.85rem', color: '#fca5a5', whiteSpace: 'pre-wrap' }}>
                                    <strong style={{ display: 'block', marginBottom: '0.5rem', color: '#ef4444' }}>⚠️ Negotiation Copilot Blocked</strong>
                                    {draft.replace('ERROR:', '').trim()}
                                </div>
                            ) : (
                                <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', fontSize: '0.85rem', color: '#e2e8f0', maxHeight: '200px', overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                                    {draft}
                                </div>
                            )
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
