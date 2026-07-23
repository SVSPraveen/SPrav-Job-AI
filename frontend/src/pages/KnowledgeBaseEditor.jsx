import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Save, Plus, Trash2, X } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

const KnowledgeBaseEditor = () => {
  const [activeTab, setActiveTab] = useState('personal');
  const [kbData, setKbData] = useState({
    personal: {},
    work_history: [],
    projects: [],
    education: [],
    certifications: [],
    resume_bullets: [],
    skills: { languages: [], frameworks: [], tools: [] }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchKb();
  }, []);

  const fetchKb = async () => {
    try {
      const res = await axios.get(`${API_BASE}/kb`);
      // Ensure arrays/objects exist if missing
      const data = res.data;
      if (!data.work_history) data.work_history = [];
      if (!data.projects) data.projects = [];
      if (!data.education) data.education = [];
      if (!data.certifications) data.certifications = [];
      if (!data.resume_bullets) data.resume_bullets = [];
      if (!data.skills) data.skills = { languages: [], frameworks: [], tools: [] };
      if (!data.personal) data.personal = {};
      setKbData(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const saveKb = async () => {
    try {
      await axios.post(`${API_BASE}/kb`, { kb_data: kbData });
      alert('Knowledge Base saved successfully to me.json!');
    } catch (e) {
      console.error(e);
      alert('Error saving KB data');
    }
  };

  const handlePersonalChange = (field, value) => {
    setKbData(prev => ({
      ...prev,
      personal: { ...prev.personal, [field]: value }
    }));
  };

  const handleArrayChange = (arrayName, index, field, value) => {
    setKbData(prev => {
      const newArray = [...prev[arrayName]];
      newArray[index] = { ...newArray[index], [field]: value };
      return { ...prev, [arrayName]: newArray };
    });
  };

  const addArrayItem = (arrayName, defaultItem) => {
    setKbData(prev => ({
      ...prev,
      [arrayName]: [...prev[arrayName], { id: `${arrayName}_${Date.now()}`, ...defaultItem }]
    }));
  };

  const removeArrayItem = (arrayName, index) => {
    setKbData(prev => {
      const newArray = [...prev[arrayName]];
      newArray.splice(index, 1);
      return { ...prev, [arrayName]: newArray };
    });
  };

  // Bullets Logic
  const getBulletsForParent = (parentId) => {
    return kbData.resume_bullets.filter(b => b.parent_id === parentId);
  };

  const addBullet = (parentId) => {
    setKbData(prev => ({
      ...prev,
      resume_bullets: [
        ...prev.resume_bullets,
        { id: `bullet_${Date.now()}`, parent_id: parentId, text: '', ats_keywords: [] }
      ]
    }));
  };

  const updateBullet = (bulletId, text) => {
    setKbData(prev => ({
      ...prev,
      resume_bullets: prev.resume_bullets.map(b => b.id === bulletId ? { ...b, text } : b)
    }));
  };

  const removeBullet = (bulletId) => {
    setKbData(prev => ({
      ...prev,
      resume_bullets: prev.resume_bullets.filter(b => b.id !== bulletId)
    }));
  };

  const handleSkillChange = (category, value) => {
    const list = value.split(',').map(s => s.trim()).filter(Boolean);
    setKbData(prev => ({
      ...prev,
      skills: { ...prev.skills, [category]: list }
    }));
  };

  if (loading) return <div>Loading KB Data...</div>;

  const tabs = [
    { id: 'personal', label: 'Personal Info' },
    { id: 'work', label: 'Work History' },
    { id: 'projects', label: 'Projects' },
    { id: 'education', label: 'Education & Certs' },
    { id: 'skills', label: 'Skills' }
  ];

  return (
    <div className="kb-editor-container fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2>Knowledge Base Editor</h2>
          <p className="subtitle" style={{marginBottom: 0}}>The absolute source of truth for your AI Resume Engine.</p>
        </div>
        <button className="btn" onClick={saveKb} style={{ background: 'var(--success)' }}>
          <Save size={18} /> Save All Changes
        </button>
      </div>

      <div className="kb-tabs" style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem', marginBottom: '2rem' }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              background: 'transparent',
              border: 'none',
              color: activeTab === tab.id ? 'var(--accent)' : 'var(--text-secondary)',
              fontWeight: activeTab === tab.id ? '600' : '500',
              cursor: 'pointer',
              padding: '0.5rem 1rem',
              borderBottom: activeTab === tab.id ? '2px solid var(--accent)' : '2px solid transparent',
              transition: 'all 0.2s'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="kb-content premium-card" style={{ minHeight: '600px' }}>
        {activeTab === 'personal' && (
          <div className="fade-in">
            <h3 style={{ marginBottom: '1.5rem', color: 'var(--accent)' }}>Personal Information</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div>
                <label className="input-label">Full Name</label>
                <input className="input-field" value={kbData.personal.name || ''} onChange={e => handlePersonalChange('name', e.target.value)} />
              </div>
              <div>
                <label className="input-label">Email Address</label>
                <input className="input-field" value={kbData.personal.email || ''} onChange={e => handlePersonalChange('email', e.target.value)} />
              </div>
              <div>
                <label className="input-label">Phone Number</label>
                <input className="input-field" value={kbData.personal.phone || ''} onChange={e => handlePersonalChange('phone', e.target.value)} />
              </div>
              <div>
                <label className="input-label">Location (City, State)</label>
                <input className="input-field" value={kbData.personal.location || ''} onChange={e => handlePersonalChange('location', e.target.value)} />
              </div>
              <div>
                <label className="input-label">LinkedIn URL</label>
                <input className="input-field" value={kbData.personal.linkedin || ''} onChange={e => handlePersonalChange('linkedin', e.target.value)} />
              </div>
              <div>
                <label className="input-label">GitHub / Portfolio URL</label>
                <input className="input-field" value={kbData.personal.github || kbData.personal.portfolio || ''} onChange={e => handlePersonalChange('github', e.target.value)} />
              </div>
            </div>
            <div style={{ marginTop: '1.5rem' }}>
              <label className="input-label">Professional Summary</label>
              <textarea className="input-field" rows="4" value={kbData.personal.summary || ''} onChange={e => handlePersonalChange('summary', e.target.value)} placeholder="A brief overview of your professional brand..."></textarea>
            </div>
          </div>
        )}

        {activeTab === 'work' && (
          <div className="fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ color: 'var(--accent)' }}>Work History</h3>
              <button className="btn-small" onClick={() => addArrayItem('work_history', { company: '', role: '', start_date: '', end_date: '' })}>
                <Plus size={16} /> Add Job
              </button>
            </div>

            {kbData.work_history.map((job, idx) => (
              <div key={job.id} className="item-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <h4>Job #{idx + 1}</h4>
                  <button className="btn-icon danger" onClick={() => removeArrayItem('work_history', idx)}><Trash2 size={16} /></button>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                  <div>
                    <label className="input-label">Company</label>
                    <input className="input-field" value={job.company} onChange={e => handleArrayChange('work_history', idx, 'company', e.target.value)} />
                  </div>
                  <div>
                    <label className="input-label">Role / Title</label>
                    <input className="input-field" value={job.role} onChange={e => handleArrayChange('work_history', idx, 'role', e.target.value)} />
                  </div>
                  <div>
                    <label className="input-label">Start Date (MM/YYYY)</label>
                    <input className="input-field" value={job.start_date} onChange={e => handleArrayChange('work_history', idx, 'start_date', e.target.value)} />
                  </div>
                  <div>
                    <label className="input-label">End Date (or 'Present')</label>
                    <input className="input-field" value={job.end_date} onChange={e => handleArrayChange('work_history', idx, 'end_date', e.target.value)} />
                  </div>
                </div>

                <div className="bullets-section">
                  <h5 style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Resume Bullets for this Role</h5>
                  {getBulletsForParent(job.id).map((bullet) => (
                    <div key={bullet.id} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      <textarea 
                        className="input-field" 
                        rows="2" 
                        value={bullet.text} 
                        onChange={e => updateBullet(bullet.id, e.target.value)}
                        placeholder="Bullet point text..."
                      />
                      <button className="btn-icon danger" onClick={() => removeBullet(bullet.id)}><X size={16} /></button>
                    </div>
                  ))}
                  <button className="btn-small outline" onClick={() => addBullet(job.id)} style={{ marginTop: '0.5rem' }}>
                    <Plus size={14} /> Add Bullet
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'projects' && (
          <div className="fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ color: 'var(--accent)' }}>Projects</h3>
              <button className="btn-small" onClick={() => addArrayItem('projects', { name: '', tagline: '', start_date: '', end_date: '' })}>
                <Plus size={16} /> Add Project
              </button>
            </div>

            {kbData.projects.map((proj, idx) => (
              <div key={proj.id} className="item-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <h4>Project #{idx + 1}</h4>
                  <button className="btn-icon danger" onClick={() => removeArrayItem('projects', idx)}><Trash2 size={16} /></button>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                  <div>
                    <label className="input-label">Project Name</label>
                    <input className="input-field" value={proj.name} onChange={e => handleArrayChange('projects', idx, 'name', e.target.value)} />
                  </div>
                  <div>
                    <label className="input-label">Tagline / Short Desc</label>
                    <input className="input-field" value={proj.tagline} onChange={e => handleArrayChange('projects', idx, 'tagline', e.target.value)} />
                  </div>
                  <div>
                    <label className="input-label">Start Date</label>
                    <input className="input-field" value={proj.start_date} onChange={e => handleArrayChange('projects', idx, 'start_date', e.target.value)} />
                  </div>
                  <div>
                    <label className="input-label">End Date</label>
                    <input className="input-field" value={proj.end_date} onChange={e => handleArrayChange('projects', idx, 'end_date', e.target.value)} />
                  </div>
                </div>

                <div className="bullets-section">
                  <h5 style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Project Bullets</h5>
                  {getBulletsForParent(proj.id).map((bullet) => (
                    <div key={bullet.id} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      <textarea 
                        className="input-field" 
                        rows="2" 
                        value={bullet.text} 
                        onChange={e => updateBullet(bullet.id, e.target.value)}
                        placeholder="Bullet point text..."
                      />
                      <button className="btn-icon danger" onClick={() => removeBullet(bullet.id)}><X size={16} /></button>
                    </div>
                  ))}
                  <button className="btn-small outline" onClick={() => addBullet(proj.id)} style={{ marginTop: '0.5rem' }}>
                    <Plus size={14} /> Add Bullet
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'education' && (
          <div className="fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ color: 'var(--accent)' }}>Education</h3>
              <button className="btn-small" onClick={() => addArrayItem('education', { institution: '', degree: '', year: '' })}>
                <Plus size={16} /> Add Education
              </button>
            </div>
            
            {kbData.education.map((edu, idx) => (
              <div key={edu.id || idx} className="item-card" style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                <div style={{ flex: 1 }}>
                  <label className="input-label">Institution</label>
                  <input className="input-field" value={edu.institution} onChange={e => handleArrayChange('education', idx, 'institution', e.target.value)} />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="input-label">Degree / Major</label>
                  <input className="input-field" value={edu.degree} onChange={e => handleArrayChange('education', idx, 'degree', e.target.value)} />
                </div>
                <div style={{ flex: 0.5 }}>
                  <label className="input-label">Year</label>
                  <input className="input-field" value={edu.year} onChange={e => handleArrayChange('education', idx, 'year', e.target.value)} />
                </div>
                <button className="btn-icon danger" onClick={() => removeArrayItem('education', idx)}><Trash2 size={16} /></button>
              </div>
            ))}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '2.5rem 0 1.5rem 0' }}>
              <h3 style={{ color: 'var(--accent)' }}>Certifications</h3>
              <button className="btn-small" onClick={() => addArrayItem('certifications', { name: '', issuer: '', date_earned: '' })}>
                <Plus size={16} /> Add Cert
              </button>
            </div>

            {kbData.certifications.map((cert, idx) => (
              <div key={cert.id || idx} className="item-card" style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                <div style={{ flex: 1 }}>
                  <label className="input-label">Certificate Name</label>
                  <input className="input-field" value={cert.name} onChange={e => handleArrayChange('certifications', idx, 'name', e.target.value)} />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="input-label">Issuer</label>
                  <input className="input-field" value={cert.issuer} onChange={e => handleArrayChange('certifications', idx, 'issuer', e.target.value)} />
                </div>
                <div style={{ flex: 0.5 }}>
                  <label className="input-label">Year Earned</label>
                  <input className="input-field" value={cert.date_earned} onChange={e => handleArrayChange('certifications', idx, 'date_earned', e.target.value)} />
                </div>
                <button className="btn-icon danger" onClick={() => removeArrayItem('certifications', idx)}><Trash2 size={16} /></button>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'skills' && (
          <div className="fade-in">
            <h3 style={{ marginBottom: '1.5rem', color: 'var(--accent)' }}>Skills Arsenal</h3>
            <p className="subtitle" style={{marginBottom: '2rem'}}>Comma-separated list of your technical skills.</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
              <div>
                <label className="input-label">Languages</label>
                <input className="input-field" value={kbData.skills.languages?.join(', ') || ''} onChange={e => handleSkillChange('languages', e.target.value)} placeholder="Python, JavaScript, Go..." />
              </div>
              <div>
                <label className="input-label">Frameworks</label>
                <input className="input-field" value={kbData.skills.frameworks?.join(', ') || ''} onChange={e => handleSkillChange('frameworks', e.target.value)} placeholder="React, Django, FastAPI..." />
              </div>
              <div>
                <label className="input-label">Tools & Platforms</label>
                <input className="input-field" value={kbData.skills.tools?.join(', ') || ''} onChange={e => handleSkillChange('tools', e.target.value)} placeholder="AWS, Docker, Git..." />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeBaseEditor;
