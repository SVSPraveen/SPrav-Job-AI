import React from 'react';
import { Users, Mail, Target, ExternalLink } from 'lucide-react';

export default function ReferralAssist({ contactsRaw, company }) {
    if (!contactsRaw) return null;
    
    let contacts = [];
    try {
        contacts = typeof contactsRaw === 'string' ? JSON.parse(contactsRaw) : contactsRaw;
    } catch (e) {
        return null;
    }

    if (!contacts || contacts.length === 0) return null;

    return (
        <div style={{ marginTop: '2rem' }}>
            <h3 style={{ marginBottom: '0.75rem', color: 'var(--accent)', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Users size={18} /> Discovered Referrals & Hiring Managers
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
                SPrav found these contacts at {company}. Use the pre-filled LinkedIn search links or direct emails (if inferred) to send an outreach note.
            </p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {contacts.map((contact, i) => (
                    <div key={i} style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                                <strong style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>{contact.name || "Unknown"}</strong>
                                {contact.tier === 'hiring_manager' && (
                                    <span style={{ background: 'rgba(251, 191, 36, 0.2)', color: '#fbbf24', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                                        <Target size={12}/> Hiring Manager/Eng Lead
                                    </span>
                                )}
                                {contact.tier === 'employee' && (
                                    <span style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>
                                        Employee
                                    </span>
                                )}
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                                {contact.current_role || "Employee"} • {contact.location || "Location unknown"}
                            </div>
                        </div>
                        
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            {contact.email && contact.email.includes('@') && (
                                <a 
                                    href={`mailto:${contact.email}`}
                                    className="btn btn-secondary"
                                    style={{ padding: '0.5rem', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
                                    title="Send Email"
                                >
                                    <Mail size={16} /> <span className="hide-on-mobile">Email</span>
                                </a>
                            )}
                            <a 
                                href={contact.url || `https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(contact.name + " " + company)}`}
                                target="_blank"
                                rel="noreferrer"
                                className="btn"
                                style={{ background: '#0a66c2', padding: '0.5rem', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
                            >
                                <ExternalLink size={16} /> <span className="hide-on-mobile">LinkedIn</span>
                            </a>
                        </div>
                    </div>
                ))}
            </div>
            
            <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.2)', borderRadius: '6px', fontSize: '0.85rem', color: '#93c5fd' }}>
                <strong>Tip:</strong> Always mention a specific project from the company's engineering blog or recent news to get a higher response rate. Check the Drafts section for inspiration.
            </div>
        </div>
    );
}
