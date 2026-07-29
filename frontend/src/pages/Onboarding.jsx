import React, { useState } from 'react';
import axios from 'axios';
import { UploadCloud, Link, CheckCircle, ArrowRight, Save, AlertTriangle } from 'lucide-react';
import './Onboarding.css';

const API_BASE = 'http://localhost:8000/api/onboarding';

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Inputs
  const [resumeFile, setResumeFile] = useState(null);
  const [githubInput, setGithubInput] = useState('');
  const [githubToken, setGithubToken] = useState('');

  // Payload state
  const [payload, setPayload] = useState(null);

  const handleFileUpload = (e) => {
    if (e.target.files.length > 0) setResumeFile(e.target.files[0]);
  };

  const handleExtract = async () => {
    if (!resumeFile && !githubInput.trim()) {
      alert("Please provide at least a resume or GitHub profile.");
      return;
    }
    
    setLoading(true);
    setStep(2); // Loading step

    const fd = new FormData();
    if (resumeFile) fd.append('file', resumeFile);
    if (githubInput.trim()) fd.append('github', githubInput.trim());
    if (githubToken.trim()) fd.append('github_token', githubToken.trim());

    try {
      // In Vite proxy, /api goes to backend
      const res = await axios.post(`${API_BASE}/extract`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setPayload(res.data);
      setStep(3); // Review step
    } catch (err) {
      console.error(err);
      alert(`Extraction failed: ${err.response?.data?.detail || err.message}`);
      setStep(1);
    } finally {
      setLoading(false);
    }
  };

  const handleMerge = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/merge`, payload);
      alert("✅ Knowledge Base successfully populated! The engine is ready.");
      window.location.reload();
    } catch (err) {
      console.error(err);
      alert(`Merge failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const updateJobBullet = (jobIndex, bulletIndex, newText) => {
    const newPayload = { ...payload };
    newPayload.jobs[jobIndex].proposed_bullets[bulletIndex].text = newText;
    setPayload(newPayload);
  };

  const updateProjectBullet = (projIndex, bulletIndex, newText) => {
    const newPayload = { ...payload };
    newPayload.projects[projIndex].proposed_bullets[bulletIndex].text = newText;
    setPayload(newPayload);
  };

  const getFlagColor = (flag) => {
    if (flag === 'Verified') return '#4ade80';
    if (flag === 'No Metrics') return '#facc15';
    if (flag === 'Qualitative Overclaim' || flag === 'Garbled') return '#f87171';
    if (flag === 'No README') return '#94a3b8';
    return '#94a3b8';
  };

  return (
    <div className="onboarding-container fade-in">
      <h2>Knowledge Base Onboarding</h2>
      <p className="subtitle">Populate your Knowledge Base using your existing Resume and GitHub.</p>

      <div className="progress-bar" style={{ maxWidth: '600px', margin: '0 auto 2.5rem auto' }}>
        <div className={`progress-step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
          <div className="step-num">1</div>
          <div className="step-label">Upload</div>
        </div>
        <div className={`progress-step ${step >= 3 ? 'active' : ''} ${step > 3 ? 'completed' : ''}`}>
          <div className="step-num">2</div>
          <div className="step-label">Review</div>
        </div>
        <div className={`progress-step ${step >= 4 ? 'active' : ''}`}>
          <div className="step-num">3</div>
          <div className="step-label">Done</div>
        </div>
      </div>

      <div className="premium-card" style={{ position: 'relative', minHeight: '320px' }}>
        {loading && <div className="loader-overlay"><span>Extracting & Validating data... This may take a minute.</span></div>}

        {step === 1 && (
          <div className="step-content">
            <h3><UploadCloud size={20} /> Upload Resume</h3>
            <div className="drop-zone" onClick={() => document.getElementById('resume-input').click()}>
              {resumeFile ? <span>📄 {resumeFile.name}</span> : <span>Click or drag & drop your resume here (.pdf or .docx)</span>}
            </div>
            <input id="resume-input" type="file" accept=".pdf,.docx" style={{ display: 'none' }} onChange={handleFileUpload} />
            
            <h3 style={{ marginTop: '2rem' }}><Link size={20} /> Sync GitHub Projects</h3>
            <div className="form-group">
              <label>GitHub Username or Repo URLs (comma-separated)</label>
              <input
                type="text"
                value={githubInput}
                onChange={e => setGithubInput(e.target.value)}
                placeholder="octocat OR https://github.com/octocat/Hello-World"
              />
            </div>
            <div className="form-group">
              <label>Personal Access Token <span className="hint">(Optional — bypasses rate limits)</span></label>
              <input type="password" value={githubToken} onChange={e => setGithubToken(e.target.value)} placeholder="ghp_..." />
            </div>

            <div className="actions">
              <div />
              <button className="btn" onClick={handleExtract} disabled={!resumeFile && !githubInput.trim()}>
                Extract & Validate <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {step === 3 && payload && (
          <div className="step-content review-step">
            <h3><CheckCircle size={20} /> Review Proposed Bullets</h3>
            <p>Please review the bullets extracted. The AI Engine has run validation logic against the source texts. Pay close attention to items flagged as <strong>Qualitative Overclaim</strong> or <strong>No Metrics</strong>.</p>
            
            {payload.jobs?.length > 0 && (
              <div className="manual-section">
                <h4>💼 Work History (From Resume)</h4>
                {payload.jobs.map((job, jobIdx) => (
                  <div key={jobIdx} className="manual-row" style={{ marginBottom: '1.5rem' }}>
                    <div className="manual-row-header">
                      <span>{job.company} — {job.role} ({job.start_date} to {job.end_date})</span>
                    </div>
                    <div className="bullets-section">
                      {job.proposed_bullets.map((b, bIdx) => (
                        <div key={bIdx} style={{ marginBottom: '1rem', background: 'rgba(0,0,0,0.15)', padding: '0.8rem', borderRadius: '6px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: getFlagColor(b.flag), display: 'flex', alignItems: 'center', gap: '4px' }}>
                              {(b.flag !== 'Verified') && <AlertTriangle size={12} />} [{b.flag}]
                            </span>
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Reason: {b.reason}</span>
                          </div>
                          <textarea
                            style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', resize: 'vertical' }}
                            rows={2}
                            value={b.text}
                            onChange={(e) => updateJobBullet(jobIdx, bIdx, e.target.value)}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {payload.projects?.length > 0 && (
              <div className="manual-section">
                <h4>💻 GitHub Projects</h4>
                {payload.projects.map((proj, projIdx) => (
                  <div key={projIdx} className="manual-row" style={{ marginBottom: '1.5rem' }}>
                    <div className="manual-row-header">
                      <span>{proj.name}</span>
                    </div>
                    {proj.description && <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>{proj.description}</p>}
                    <div className="bullets-section">
                      {proj.proposed_bullets.map((b, bIdx) => (
                        <div key={bIdx} style={{ marginBottom: '1rem', background: 'rgba(0,0,0,0.15)', padding: '0.8rem', borderRadius: '6px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: getFlagColor(b.flag), display: 'flex', alignItems: 'center', gap: '4px' }}>
                              {(b.flag !== 'Verified') && <AlertTriangle size={12} />} [{b.flag}]
                            </span>
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Reason: {b.reason}</span>
                          </div>
                          <textarea
                            style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', resize: 'vertical' }}
                            rows={2}
                            value={b.text}
                            onChange={(e) => updateProjectBullet(projIdx, bIdx, e.target.value)}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="actions">
              <button className="btn outline" onClick={() => setStep(1)}>Back</button>
              <button className="btn" onClick={handleMerge} style={{ background: 'var(--success)' }}>
                <Save size={16} /> Save & Merge to Knowledge Base
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
