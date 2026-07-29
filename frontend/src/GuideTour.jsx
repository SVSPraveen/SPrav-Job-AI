import React, { useState } from 'react';
import { HelpCircle, X, ChevronRight, CheckCircle, ChevronDown, ChevronUp } from 'lucide-react';
import guideData from './guideContent.json';

function GuideTour({ currentTab }) {
    const [isOpen, setIsOpen] = useState(false);
    const [hasSeenPing, setHasSeenPing] = useState(() => localStorage.getItem('sprav_guide_ping_seen') === 'true');
    const [isHovered, setIsHovered] = useState(false);
    
    const [isFirstTime, setIsFirstTime] = useState(() => localStorage.getItem('sprav_setup_complete') !== 'true');
    const [currentStep, setCurrentStep] = useState(0);
    const [expandedFaq, setExpandedFaq] = useState(null);

    const handleClick = () => {
        if (!hasSeenPing) {
            localStorage.setItem('sprav_guide_ping_seen', 'true');
            setHasSeenPing(true);
        }
        setIsOpen(true);
    };

    const finishOnboarding = () => {
        localStorage.setItem('sprav_setup_complete', 'true');
        setIsFirstTime(false);
        setIsOpen(false);
    };

    if (!isOpen) {
        return (
            <>
            <style>{`
                @keyframes guide-ping { 
                    0% { transform: scale(1); opacity: 0.8; }
                    75%, 100% { transform: scale(1.6); opacity: 0; }
                }
            `}</style>
            <button 
                id="guide_tour"
                onClick={handleClick}
                style={{
                    position: 'fixed',
                    top: '32px',
                    right: '32px',
                    width: '56px',
                    height: '56px',
                    borderRadius: '50%',
                    background: 'var(--success)',
                    color: '#fff',
                    border: 'none',
                    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.4)',
                    cursor: 'pointer',
                    zIndex: 9999,
                    padding: 0
                }}
            >
                <div 
                    onMouseEnter={() => setIsHovered(true)} 
                    onMouseLeave={() => setIsHovered(false)}
                    style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                >
                    <HelpCircle size={28} />
                    
                    {isHovered && (
                        <div style={{
                            position: 'absolute',
                            right: 'calc(100% + 16px)',
                            background: 'var(--bg-surface-hover)',
                            padding: '6px 12px',
                            borderRadius: '6px',
                            border: '1px solid var(--border-strong)',
                            color: 'var(--text-primary)',
                            fontSize: '0.85rem',
                            whiteSpace: 'nowrap',
                            pointerEvents: 'none'
                        }}>
                            Guide Tour
                        </div>
                    )}
                    
                    {!hasSeenPing && (
                        <div style={{
                            position: 'absolute',
                            top: '-2px', left: '-2px', right: '-2px', bottom: '-2px',
                            borderRadius: '50%',
                            border: '2px solid var(--success)',
                            animation: 'guide-ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
                            pointerEvents: 'none'
                        }} />
                    )}
                </div>
            </button>
            </>
        );
    }

    const renderOnboarding = () => {
        const steps = guideData.onboarding.steps;
        const step = steps[currentStep];
        
        return (
            <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
                <div style={{ flex: 1 }}>
                    <div style={{ 
                        fontSize: '0.8rem', 
                        color: 'var(--text-muted)', 
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        marginBottom: '0.5rem'
                    }}>
                        Step {currentStep + 1} of {steps.length}
                    </div>
                    <h3 style={{ margin: '0 0 1rem 0', color: 'var(--text-primary)', fontSize: '1.3rem' }}>{step.title}</h3>
                    <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: '1.6' }}>
                        {step.desc}
                    </p>
                </div>
                
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: 'auto', paddingTop: '2rem' }}>
                    {currentStep > 0 && (
                        <button 
                            onClick={() => setCurrentStep(prev => prev - 1)}
                            style={{
                                padding: '10px 16px',
                                background: 'transparent',
                                border: '1px solid var(--border-strong)',
                                color: 'var(--text-secondary)',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                fontWeight: '500'
                            }}
                        >
                            Back
                        </button>
                    )}
                    
                    {currentStep < steps.length - 1 ? (
                        <button 
                            onClick={() => setCurrentStep(prev => prev + 1)}
                            style={{
                                flex: 1,
                                padding: '10px 16px',
                                background: 'var(--success)',
                                border: 'none',
                                color: '#fff',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                fontWeight: '600',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px'
                            }}
                        >
                            Next Step <ChevronRight size={18} />
                        </button>
                    ) : (
                        <button 
                            onClick={finishOnboarding}
                            style={{
                                flex: 1,
                                padding: '10px 16px',
                                background: 'var(--success)',
                                border: 'none',
                                color: '#fff',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                fontWeight: '600',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                boxShadow: '0 4px 12px rgba(16, 185, 129, 0.4)'
                            }}
                        >
                            <CheckCircle size={18} /> I've saved my data, Let's go!
                        </button>
                    )}
                </div>
            </div>
        );
    };

    const renderTroubleshooting = () => {
        return (
            <div style={{ padding: '1.25rem', overflowY: 'auto', flex: 1 }}>
                <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)', fontSize: '1.2rem' }}>
                    What happened?
                </h3>
                <p style={{ margin: '0 0 1.5rem 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    Select an issue below if you got stuck somewhere.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {guideData.troubleshooting.map((item, idx) => {
                        const isExpanded = expandedFaq === idx;
                        return (
                            <div key={idx} style={{
                                background: 'var(--bg-surface-hover)',
                                border: '1px solid var(--border-strong)',
                                borderRadius: '8px',
                                overflow: 'hidden'
                            }}>
                                <button 
                                    onClick={() => setExpandedFaq(isExpanded ? null : idx)}
                                    style={{
                                        width: '100%',
                                        padding: '1rem',
                                        background: 'transparent',
                                        border: 'none',
                                        color: 'var(--text-primary)',
                                        textAlign: 'left',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        fontWeight: '500',
                                        fontSize: '0.95rem'
                                    }}
                                >
                                    <span>{item.q}</span>
                                    {isExpanded ? <ChevronUp size={18} color="var(--text-muted)" /> : <ChevronDown size={18} color="var(--text-muted)" />}
                                </button>
                                
                                {isExpanded && (
                                    <div style={{
                                        padding: '0 1rem 1rem 1rem',
                                        color: 'var(--text-secondary)',
                                        fontSize: '0.9rem',
                                        lineHeight: '1.5'
                                    }}>
                                        {item.a}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
                
                <div style={{ marginTop: '2rem', textAlign: 'center' }}>
                    <button 
                        onClick={() => {
                            setCurrentStep(0);
                            setIsFirstTime(true);
                        }}
                        style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--text-muted)',
                            textDecoration: 'underline',
                            cursor: 'pointer',
                            fontSize: '0.85rem'
                        }}
                    >
                        Restart Setup Tour
                    </button>
                </div>
            </div>
        );
    };

    return (
        <div style={{
            position: 'fixed',
            bottom: '2rem',
            right: '2rem',
            width: '380px',
            height: '500px',
            background: '#1a1d24',
            borderRadius: '16px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
            border: '1px solid rgba(255,255,255,0.1)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 9999,
            overflow: 'hidden',
            fontFamily: 'Inter, system-ui, sans-serif'
        }}>
            <div style={{
                padding: '1rem 1.25rem',
                background: 'rgba(255,255,255,0.03)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: '1px solid var(--border-strong)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <HelpCircle size={20} color="var(--success)" />
                    <strong style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                        {isFirstTime ? 'Setup Guide' : 'Troubleshooting'}
                    </strong>
                </div>
                <button 
                    onClick={() => setIsOpen(false)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px' }}
                >
                    <X size={20} />
                </button>
            </div>
            
            <div style={{ flex: 1, overflowY: 'auto' }}>
                {isFirstTime ? renderOnboarding() : renderTroubleshooting()}
            </div>
        </div>
    );
}

export default GuideTour;
