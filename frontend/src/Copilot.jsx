import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { MessageCircle, X, Send } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

function Copilot({ token, currentTab }) {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const [hasOpenedOnce, setHasOpenedOnce] = useState(
        () => localStorage.getItem('sprav_copilot_opened') === 'true'
    );

    // Auto-open on first run
    useEffect(() => {
        if (!hasOpenedOnce) {
            setTimeout(() => {
                setIsOpen(true);
                setMessages([
                    { role: 'assistant', content: "Hi! I'm your SPrav Copilot. It looks like this is your first time here. \n\nI recommend starting by going to **Settings & Auth** on the left to securely add your LinkedIn credentials so I can start scouting HR posts for you. \n\nWhat would you like help with first?" }
                ]);
                localStorage.setItem('sprav_copilot_opened', 'true');
                setHasOpenedOnce(true);
            }, 1000);
        }
    }, [hasOpenedOnce]);

    // Auto-scroll to bottom
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages, isOpen]);

    const handleSend = async (text = input) => {
        if (!text.trim()) return;
        
        const newMsg = { role: 'user', content: text };
        setMessages(prev => [...prev, newMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await axios.post(`${API_BASE}/copilot`, {
                message: text,
                page_context: currentTab
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });
            
            setMessages(prev => [...prev, { role: 'assistant', content: res.data.reply }]);
        } catch (e) {
            setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I'm having trouble connecting right now." }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    if (!isOpen) {
        return (
            <button 
                onClick={() => setIsOpen(true)}
                style={{
                    position: 'fixed',
                    bottom: '2rem',
                    right: '2rem',
                    width: '56px',
                    height: '56px',
                    borderRadius: '50%',
                    background: 'var(--accent)',
                    color: '#fff',
                    border: 'none',
                    boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 9999,
                    transition: 'transform 0.2s ease',
                }}
                onMouseOver={e => e.currentTarget.style.transform = 'scale(1.1)'}
                onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}
            >
                <MessageCircle size={28} />
            </button>
        );
    }

    return (
        <div style={{
            position: 'fixed',
            bottom: '2rem',
            right: '2rem',
            width: '380px',
            height: '600px',
            maxHeight: '80vh',
            background: '#1a1d24',
            borderRadius: '16px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
            border: '1px solid rgba(255,255,255,0.1)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 9999,
            overflow: 'hidden'
        }}>
            {/* Header */}
            <div style={{
                padding: '1rem 1.25rem',
                background: 'linear-gradient(90deg, var(--accent) 0%, #4f46e5 100%)',
                color: '#fff',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <MessageCircle size={20} />
                    <strong style={{ fontSize: '1.05rem' }}>SPrav Copilot</strong>
                </div>
                <button 
                    onClick={() => setIsOpen(false)}
                    style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', padding: '4px' }}
                >
                    <X size={20} />
                </button>
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {messages.length === 0 && !loading && (
                    <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '2rem', fontSize: '0.9rem' }}>
                        Ask me anything about SPrav, job hunting, or how to configure the AI.
                    </div>
                )}
                
                {messages.map((msg, idx) => (
                    <div key={idx} style={{
                        alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                        maxWidth: '85%',
                        background: msg.role === 'user' ? 'var(--accent)' : 'rgba(255,255,255,0.05)',
                        border: msg.role === 'user' ? 'none' : '1px solid rgba(255,255,255,0.1)',
                        padding: '0.75rem 1rem',
                        borderRadius: '12px',
                        borderBottomRightRadius: msg.role === 'user' ? '4px' : '12px',
                        borderBottomLeftRadius: msg.role === 'assistant' ? '4px' : '12px',
                        color: '#fff',
                        fontSize: '0.9rem',
                        lineHeight: '1.4'
                    }}>
                        {msg.content.split('\n').map((line, i) => (
                            <React.Fragment key={i}>
                                {line.replace(/\*\*(.*?)\*\*/g, '$1')} 
                                {i !== msg.content.split('\n').length - 1 && <br />}
                            </React.Fragment>
                        ))}
                    </div>
                ))}
                
                {loading && (
                    <div style={{ alignSelf: 'flex-start', color: 'var(--text-secondary)', fontSize: '0.85rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <div className="typing-dot"></div><div className="typing-dot"></div><div className="typing-dot"></div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Suggested Actions (if few messages) */}
            {messages.length < 3 && !loading && (
                <div style={{ padding: '0 1rem', display: 'flex', gap: '0.5rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
                    {['What should I do first?', 'How does auto-apply work?', 'Why are my jobs rejected?'].map(txt => (
                        <button key={txt} onClick={() => handleSend(txt)} style={{
                            background: 'rgba(255,255,255,0.05)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            color: 'var(--text-secondary)',
                            padding: '0.4rem 0.8rem',
                            borderRadius: '100px',
                            fontSize: '0.8rem',
                            cursor: 'pointer',
                            whiteSpace: 'nowrap'
                        }}>
                            {txt}
                        </button>
                    ))}
                </div>
            )}

            {/* Input Area */}
            <div style={{ padding: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)', display: 'flex', gap: '0.5rem' }}>
                <textarea 
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="Ask Copilot..."
                    style={{
                        flex: 1,
                        background: 'rgba(0,0,0,0.2)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '8px',
                        padding: '0.75rem',
                        color: '#fff',
                        fontSize: '0.9rem',
                        resize: 'none',
                        height: '44px',
                        fontFamily: 'inherit'
                    }}
                />
                <button 
                    onClick={() => handleSend()}
                    disabled={!input.trim() || loading}
                    style={{
                        background: 'var(--accent)',
                        border: 'none',
                        borderRadius: '8px',
                        width: '44px',
                        height: '44px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#fff',
                        cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
                        opacity: input.trim() && !loading ? 1 : 0.5
                    }}
                >
                    <Send size={18} />
                </button>
            </div>
            
            <style>{`
                .typing-dot { width: 6px; height: 6px; background: var(--text-secondary); border-radius: 50%; animation: typing 1.4s infinite ease-in-out both; }
                .typing-dot:nth-child(1) { animation-delay: -0.32s; }
                .typing-dot:nth-child(2) { animation-delay: -0.16s; }
                @keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
            `}</style>
        </div>
    );
}

export default Copilot;
