import React, { useState, useRef } from 'react';
import axios from 'axios';
import { UploadCloud, Github, Linkedin, Globe, Edit, CheckCircle, ArrowRight, Plus, Trash2 } from 'lucide-react';
import './Onboarding.css';

const API_BASE = 'http://localhost:8000/api/intake';

const EMPTY_FREELANCE = () => ({ company: '', role: 'Freelance', start_date: '', end_date: '', bullets: [''] });
const EMPTY_INTERNSHIP = () => ({ company: '', role: 'Intern', start_date: '', end_date: '', bullets: [''] });
const EMPTY_CERT = () => ({ name: '', issuer: '', date_earned: '', expires: '', credential_id: '', url: '' });

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const sourcesRef = useRef([]); // Use a ref instead of state to avoid stale closure in merge

  // Step States
  const [resumeFile, setResumeFile] = useState(null);
  const [githubInput, setGithubInput] = useState('');  // username OR comma-separated repo URLs
  const [githubToken, setGithubToken] = useState('');
  const [linkedinFile, setLinkedinFile] = useState(null);
  const [portfolioUrl, setPortfolioUrl] = useState('');

  // Step 5: Manual Entries
  const [freelanceList, setFreelanceList] = useState([]);
  const [internshipList, setInternshipList] = useState([]);
  const [certList, setCertList] = useState([]);

  // Merge Result
  const [mergeResult, setMergeResult] = useState(null);
  const [resolutions, setResolutions] = useState({});
  const [detailUpdates, setDetailUpdates] = useState({});

  const [loading, setLoading] = useState(false);

  const addSource = (data) => {
    sourcesRef.current = [...sourcesRef.current, data];
  };

  const handleFileUpload = (e, setter) => {
    if (e.target.files.length > 0) setter(e.target.files[0]);
  };

  const processSource = async (sourceType, payload) => {
    setLoading(true);
    try {
      let res;
      if (payload instanceof FormData) {
        res = await axios.post(`${API_BASE}/${sourceType}`, payload, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } else {
        res = await axios.post(`${API_BASE}/${sourceType}`, payload);
      }
      addSource(res.data.data);
      return true;
    } catch (err) {
      console.error(err);
      alert(`Error processing ${sourceType}: ${err.response?.data?.detail || err.message}`);
      return false;
    } finally {
      setLoading(false);
    }
  };

  // ── Step Handlers ──────────────────────────────────────────────────────────
  const handleResumeSubmit = async () => {
    if (!resumeFile) return setStep(2);
    const fd = new FormData();
    fd.append('file', resumeFile);
    const ok = await processSource('resume', fd);
    if (ok) setStep(2);
  };

  const handleGithubSubmit = async () => {
    if (!githubInput.trim()) return setStep(3);
    // Detect if input is comma-separated URLs or a plain username
    const trimmed = githubInput.trim();
    const isUrls = trimmed.includes('github.com/');
    const payload = isUrls
      ? { repo_urls: trimmed.split(',').map(u => u.trim()).filter(Boolean), token: githubToken }
      : { username: trimmed, token: githubToken };
    const ok = await processSource('github', payload);
    if (ok) setStep(3);
  };

  const handleLinkedinSubmit = async () => {
    if (!linkedinFile) return setStep(4);
    const fd = new FormData();
    fd.append('file', linkedinFile);
    const ok = await processSource('linkedin', fd);
    if (ok) setStep(4);
  };

  const handlePortfolioSubmit = async () => {
    if (!portfolioUrl) return setStep(5);
    const ok = await processSource('portfolio', { url: portfolioUrl });
    if (ok) setStep(5);
  };

  const handleManualAndMerge = async () => {
    const hasManual = freelanceList.length > 0 || internshipList.length > 0 || certList.length > 0;
    if (hasManual) {
      const payload = { freelance: freelanceList, internships: internshipList, certifications: certList };
      await processSource('manual', payload);
      // After processSource resolves, sourcesRef.current includes the manual data
    }
    handleMerge();
  };

  const handleMerge = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/merge`, { sources: sourcesRef.current });
      setMergeResult(res.data);
      setStep(6);
    } catch (err) {
      console.error(err);
      alert(`Error merging sources: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFinalSubmit = async () => {
    setLoading(true);
    try {
      const formattedResolutions = Object.entries(resolutions).map(([field, chosen_value]) => ({ field, chosen_value }));
      const formattedDetails = Object.entries(detailUpdates).map(([bullet_id, updated_text]) => ({ bullet_id, updated_text }));
      await axios.post(`${API_BASE}/resolve`, { resolutions: formattedResolutions, detail_updates: formattedDetails });
      alert('✅ Onboarding complete! Your Knowledge Base is fully synced. The pipeline is ready to run.');
      window.location.reload();
    } catch (err) {
      console.error(err);
      alert(`Error resolving: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // ── Repeatable row helpers ─────────────────────────────────────────────────
  const updateListItem = (setter, index, field, value) =>
    setter(prev => prev.map((item, i) => i === index ? { ...item, [field]: value } : item));

  const updateBullet = (setter, entryIndex, bulletIndex, value) =>
    setter(prev => prev.map((item, i) => i === entryIndex
      ? { ...item, bullets: item.bullets.map((b, j) => j === bulletIndex ? value : b) }
      : item
    ));

  const addBullet = (setter, entryIndex) =>
    setter(prev => prev.map((item, i) => i === entryIndex ? { ...item, bullets: [...item.bullets, ''] } : item));

  const removeBullet = (setter, entryIndex, bulletIndex) =>
    setter(prev => prev.map((item, i) => i === entryIndex
      ? { ...item, bullets: item.bullets.filter((_, j) => j !== bulletIndex) }
      : item
    ));

  // ── Progress bar ────────────────────────────────────────────────────────────
  const STEP_LABELS = ['Resume', 'GitHub', 'LinkedIn', 'Portfolio', 'Manual', 'Review'];

  return (
    <div className="onboarding-container fade-in">
      <h2>Knowledge Base Onboarding</h2>
      <p className="subtitle">Pull your full professional history from every source into a single, verified Knowledge Base.</p>

      <div className="progress-bar">
        {STEP_LABELS.map((label, i) => (
          <div key={i} className={`progress-step ${step >= i + 1 ? 'active' : ''} ${step > i + 1 ? 'completed' : ''}`}>
            <div className="step-num">{i + 1}</div>
            <div className="step-label">{label}</div>
          </div>
        ))}
      </div>

      <div className="glass-card" style={{ position: 'relative', minHeight: '320px' }}>
        {loading && <div className="loader-overlay"><span>Processing…</span></div>}

        {/* ── Step 1: Resume ── */}
        {step === 1 && (
          <div className="step-content">
            <h3><UploadCloud size={20} /> Upload Existing Resume</h3>
            <p>We extract text and send it to the extraction model. PDF or DOCX accepted.</p>
            <div className="drop-zone" onClick={() => document.getElementById('resume-input').click()}>
              {resumeFile ? <span>📄 {resumeFile.name}</span> : <span>Click or drag & drop your resume here</span>}
            </div>
            <input id="resume-input" type="file" accept=".pdf,.docx" style={{ display: 'none' }} onChange={e => handleFileUpload(e, setResumeFile)} />
            <div className="actions">
              <button className="btn outline" onClick={() => setStep(2)}>Skip</button>
              <button className="btn" onClick={handleResumeSubmit} disabled={!resumeFile}>
                Process Resume <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 2: GitHub ── */}
        {step === 2 && (
          <div className="step-content">
            <h3><Github size={20} /> Sync GitHub Projects</h3>
            <p>Enter your GitHub username to import all your public repos, or paste comma-separated repo URLs for specific projects only.</p>
            <div className="form-group">
              <label>GitHub Username <em>or</em> repo URLs (comma-separated)</label>
              <input
                type="text"
                value={githubInput}
                onChange={e => setGithubInput(e.target.value)}
                placeholder="octocat   OR   https://github.com/octocat/Hello-World, https://github.com/octocat/Spoon-Knife"
              />
            </div>
            <div className="form-group">
              <label>Personal Access Token <span className="hint">(Optional — boosts rate limit from 60/hr to 5000/hr)</span></label>
              <input type="password" value={githubToken} onChange={e => setGithubToken(e.target.value)} placeholder="ghp_…" />
            </div>
            <div className="actions">
              <button className="btn outline" onClick={() => setStep(3)}>Skip</button>
              <button className="btn" onClick={handleGithubSubmit} disabled={!githubInput.trim()}>
                Sync GitHub <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: LinkedIn ── */}
        {step === 3 && (
          <div className="step-content">
            <h3><Linkedin size={20} /> LinkedIn Data Export</h3>
            <p>
              We never scrape LinkedIn directly — that would violate ToS and risk your account.
              Instead, export your data from <strong>LinkedIn Settings → Data Privacy → Get a copy of your data → All data</strong>,
              then upload the ZIP here.
            </p>
            <div className="drop-zone" onClick={() => document.getElementById('li-input').click()}>
              {linkedinFile ? <span>📦 {linkedinFile.name}</span> : <span>Click to select your LinkedIn export ZIP</span>}
            </div>
            <input id="li-input" type="file" accept=".zip" style={{ display: 'none' }} onChange={e => handleFileUpload(e, setLinkedinFile)} />
            <div className="actions">
              <button className="btn outline" onClick={() => setStep(4)}>Skip</button>
              <button className="btn" onClick={handleLinkedinSubmit} disabled={!linkedinFile}>
                Process LinkedIn <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 4: Portfolio ── */}
        {step === 4 && (
          <div className="step-content">
            <h3><Globe size={20} /> Portfolio Website</h3>
            <p>We'll scrape your portfolio site for project cards. All extracted projects start as <em>unconfirmed</em> — you'll review them in the final step.</p>
            <div className="form-group">
              <label>Portfolio URL</label>
              <input type="url" value={portfolioUrl} onChange={e => setPortfolioUrl(e.target.value)} placeholder="https://yourname.dev" />
            </div>
            <div className="actions">
              <button className="btn outline" onClick={() => setStep(5)}>Skip</button>
              <button className="btn" onClick={handlePortfolioSubmit} disabled={!portfolioUrl.trim()}>
                Scan Portfolio <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 5: Manual Entries ── */}
        {step === 5 && (
          <div className="step-content">
            <h3><Edit size={20} /> Manual Entries</h3>
            <p>Anything not in the above sources — freelance clients, internships, or certifications.</p>

            {/* Freelance rows */}
            <div className="manual-section">
              <div className="manual-section-header">
                <h4>Freelance / Contract</h4>
                <button className="btn-icon" onClick={() => setFreelanceList(p => [...p, EMPTY_FREELANCE()])}>
                  <Plus size={14} /> Add
                </button>
              </div>
              {freelanceList.map((entry, i) => (
                <div key={i} className="manual-row">
                  <div className="manual-row-header">
                    <span>Freelance #{i + 1}</span>
                    <button className="btn-icon danger" onClick={() => setFreelanceList(p => p.filter((_, j) => j !== i))}><Trash2 size={14} /></button>
                  </div>
                  <div className="manual-grid">
                    <input placeholder="Client / Company" value={entry.company} onChange={e => updateListItem(setFreelanceList, i, 'company', e.target.value)} />
                    <input placeholder="Role" value={entry.role} onChange={e => updateListItem(setFreelanceList, i, 'role', e.target.value)} />
                    <input placeholder="Start date (YYYY-MM)" value={entry.start_date} onChange={e => updateListItem(setFreelanceList, i, 'start_date', e.target.value)} />
                    <input placeholder="End date or 'Present'" value={entry.end_date} onChange={e => updateListItem(setFreelanceList, i, 'end_date', e.target.value)} />
                  </div>
                  <div className="bullets-section">
                    <label>Achievements / Bullets</label>
                    {entry.bullets.map((b, j) => (
                      <div key={j} className="bullet-row">
                        <input placeholder="Describe what you did (include a number if you have one)" value={b} onChange={e => updateBullet(setFreelanceList, i, j, e.target.value)} />
                        <button className="btn-icon danger" onClick={() => removeBullet(setFreelanceList, i, j)}><Trash2 size={12} /></button>
                      </div>
                    ))}
                    <button className="btn-icon" style={{ marginTop: '4px' }} onClick={() => addBullet(setFreelanceList, i)}><Plus size={12} /> Add bullet</button>
                  </div>
                </div>
              ))}
            </div>

            {/* Internship rows */}
            <div className="manual-section">
              <div className="manual-section-header">
                <h4>Internships</h4>
                <button className="btn-icon" onClick={() => setInternshipList(p => [...p, EMPTY_INTERNSHIP()])}>
                  <Plus size={14} /> Add
                </button>
              </div>
              {internshipList.map((entry, i) => (
                <div key={i} className="manual-row">
                  <div className="manual-row-header">
                    <span>Internship #{i + 1}</span>
                    <button className="btn-icon danger" onClick={() => setInternshipList(p => p.filter((_, j) => j !== i))}><Trash2 size={14} /></button>
                  </div>
                  <div className="manual-grid">
                    <input placeholder="Company" value={entry.company} onChange={e => updateListItem(setInternshipList, i, 'company', e.target.value)} />
                    <input placeholder="Role" value={entry.role} onChange={e => updateListItem(setInternshipList, i, 'role', e.target.value)} />
                    <input placeholder="Start date (YYYY-MM)" value={entry.start_date} onChange={e => updateListItem(setInternshipList, i, 'start_date', e.target.value)} />
                    <input placeholder="End date" value={entry.end_date} onChange={e => updateListItem(setInternshipList, i, 'end_date', e.target.value)} />
                  </div>
                  <div className="bullets-section">
                    <label>Achievements / Bullets</label>
                    {entry.bullets.map((b, j) => (
                      <div key={j} className="bullet-row">
                        <input placeholder="Describe what you did" value={b} onChange={e => updateBullet(setInternshipList, i, j, e.target.value)} />
                        <button className="btn-icon danger" onClick={() => removeBullet(setInternshipList, i, j)}><Trash2 size={12} /></button>
                      </div>
                    ))}
                    <button className="btn-icon" style={{ marginTop: '4px' }} onClick={() => addBullet(setInternshipList, i)}><Plus size={12} /> Add bullet</button>
                  </div>
                </div>
              ))}
            </div>

            {/* Certifications rows */}
            <div className="manual-section">
              <div className="manual-section-header">
                <h4>Certifications</h4>
                <button className="btn-icon" onClick={() => setCertList(p => [...p, EMPTY_CERT()])}>
                  <Plus size={14} /> Add
                </button>
              </div>
              {certList.map((cert, i) => (
                <div key={i} className="manual-row">
                  <div className="manual-row-header">
                    <span>Cert #{i + 1}</span>
                    <button className="btn-icon danger" onClick={() => setCertList(p => p.filter((_, j) => j !== i))}><Trash2 size={14} /></button>
                  </div>
                  <div className="manual-grid cert-grid">
                    <input placeholder="Certification name" value={cert.name} onChange={e => updateListItem(setCertList, i, 'name', e.target.value)} />
                    <input placeholder="Issuing body (e.g. Amazon)" value={cert.issuer} onChange={e => updateListItem(setCertList, i, 'issuer', e.target.value)} />
                    <input placeholder="Date earned (YYYY-MM)" value={cert.date_earned} onChange={e => updateListItem(setCertList, i, 'date_earned', e.target.value)} />
                    <input placeholder="Expires (YYYY-MM or blank)" value={cert.expires} onChange={e => updateListItem(setCertList, i, 'expires', e.target.value)} />
                    <input placeholder="Credential ID" value={cert.credential_id} onChange={e => updateListItem(setCertList, i, 'credential_id', e.target.value)} />
                    <input placeholder="Verification URL" value={cert.url} onChange={e => updateListItem(setCertList, i, 'url', e.target.value)} />
                  </div>
                </div>
              ))}
            </div>

            <div className="actions">
              <button className="btn outline" onClick={handleMerge}>Skip & Merge Now</button>
              <button className="btn" onClick={handleManualAndMerge}>
                Save & Merge All Sources <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 6: Review & Resolve ── */}
        {step === 6 && mergeResult && (
          <div className="step-content review-step">
            <h3><CheckCircle size={20} /> Review & Resolve</h3>

            {mergeResult.pending_conflicts?.length > 0 && (
              <div className="conflict-section">
                <h4>⚠️ Merge Conflicts — Pick the correct value</h4>
                {mergeResult.pending_conflicts.map((c, i) => (
                  <div key={i} className="conflict-item">
                    <strong className="conflict-field">{c.field}</strong>
                    <div className="conflict-options">
                      {c.values.map((v, j) => (
                        <label key={j} className={resolutions[c.field] === v.value ? 'selected' : ''}>
                          <input
                            type="radio"
                            name={c.field}
                            value={v.value}
                            onChange={() => setResolutions({ ...resolutions, [c.field]: v.value })}
                          />
                          <span className="source-badge">{v.source}</span>
                          <span>{v.value}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {mergeResult.needs_detail?.length > 0 && (
              <div className="detail-section">
                <h4>📊 Missing Metrics — Add numbers now for better ATS scores</h4>
                <p>The XYZ formula can only write what you give it. These bullets have no measurable outcome yet.</p>
                {mergeResult.needs_detail.map((d, i) => (
                  <div key={i} className="detail-item">
                    <p className="detail-prompt">💡 {d.prompt}</p>
                    <p className="detail-context">
                      <em>{d.parent_role}</em> @ <strong>{d.parent_company}</strong>
                    </p>
                    <textarea
                      rows={2}
                      defaultValue={d.current_text}
                      placeholder="Rewrite with a metric: %, time saved, users, scale..."
                      onChange={e => setDetailUpdates({ ...detailUpdates, [d.bullet_id]: e.target.value })}
                    />
                  </div>
                ))}
              </div>
            )}

            {(!mergeResult.pending_conflicts?.length && !mergeResult.needs_detail?.length) && (
              <div className="all-clear">
                <CheckCircle size={48} color="var(--success)" />
                <p>All clear — no conflicts and all bullets have measurable outcomes!</p>
              </div>
            )}

            <div className="actions">
              <button className="btn" onClick={handleFinalSubmit} style={{ background: 'var(--success)', width: '100%' }}>
                ✅ Save Knowledge Base & Complete Onboarding
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
