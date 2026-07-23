import { useState, useEffect } from 'react'
import axios from 'axios'
import { Briefcase, LayoutDashboard, Database, Activity, Search, Send, Mail, CheckCircle, Settings, BarChart2, Target, Eye } from 'lucide-react'
import ManualReview from './pages/ManualReview'
import KnowledgeBaseEditor from './pages/KnowledgeBaseEditor'
import Onboarding from './pages/Onboarding'
import ApplicationScope from './pages/ApplicationScope'
import WatchlistManager from './pages/WatchlistManager'
import Settings from './pages/Settings'
import AuthGate from './AuthGate'
import HumanApply from './HumanApply'
import Copilot from './Copilot'
import './index.css'

const API_BASE = 'http://localhost:8000/api'

function App() {
  const [activeTab, setActiveTab] = useState('home')
  const [metrics, setMetrics] = useState(null)
  const [jobs, setJobs] = useState([])
  const [sysConfig, setSysConfig] = useState({threshold: 4.0, filter_prompt: "", resume_prompt: "", max_applications_per_day: 30, target_salary: ""})
  const [frictionData, setFrictionData] = useState([])
  const [salaryData, setSalaryData] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('sprav_token') || null)

  useEffect(() => {
    if (token) {
      localStorage.setItem('sprav_token', token)
      axios.interceptors.request.use(config => {
        config.headers.Authorization = `Bearer ${token}`
        return config
      })
      fetchMetrics()
      fetchJobs()
      fetchConfig()
    }
  }, [token])

  if (!token) {
    return <AuthGate setToken={setToken} />
  }

  const fetchAnalytics = async () => {
    try {
      const [frictionRes, salaryRes] = await Promise.all([
        axios.get(`${API_BASE}/analytics/friction`),
        axios.get(`${API_BASE}/analytics/salary-gaps`)
      ])
      setFrictionData(frictionRes.data?.data || [])
      setSalaryData(salaryRes.data?.data || null)
    } catch (e) { console.error(e) }
  }

  const fetchConfig = async () => {
    try {
      const res = await axios.get(`${API_BASE}/config`)
      setSysConfig(res.data)
    } catch (e) { console.error(e) }
  }

  const saveConfig = async () => {
    try {
      await axios.post(`${API_BASE}/config`, sysConfig)
      alert("System Configuration saved successfully!")
    } catch (e) { console.error(e) }
  }



  const fetchMetrics = async () => {
    try {
      const res = await axios.get(`${API_BASE}/metrics`)
      setMetrics(res.data)
    } catch (e) { console.error(e) }
  }

  const fetchJobs = async () => {
    try {
      const res = await axios.get(`${API_BASE}/jobs`)
      setJobs(res.data)
    } catch (e) { console.error(e) }
  }

  const triggerAction = async (action) => {
    try {
      await axios.post(`${API_BASE}/action/${action}`)
      alert(`Triggered ${action} in background! Check terminal logs.`)
    } catch (e) { console.error(e) }
  }



  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <div className="sidebar">
        <h1><Briefcase size={28} /> AutoJob AI</h1>
        <div style={{marginTop: '2rem'}}>
          <div className={`nav-item ${activeTab === 'home' ? 'active' : ''}`} onClick={() => setActiveTab('home')}>
            <LayoutDashboard size={20} /> Dashboard
          </div>
          <div className={`nav-item ${activeTab === 'kb' ? 'active' : ''}`} onClick={() => setActiveTab('kb')}>
            <Database size={20} /> Knowledge Base
          </div>
          <div className={`nav-item ${activeTab === 'onboarding' ? 'active' : ''}`} onClick={() => setActiveTab('onboarding')} style={{ paddingLeft: '3rem', fontSize: '0.9rem' }}>
            ↳ Rebuild from Sources
          </div>
          <div className={`nav-item ${activeTab === 'portal' ? 'active' : ''}`} onClick={() => setActiveTab('portal')}>
            <Activity size={20} /> Job Portal
          </div>
          <div className={`nav-item ${activeTab === 'manual' ? 'active' : ''}`} onClick={() => setActiveTab('manual')}>
            <CheckCircle size={20} /> Action Required
          </div>
          <div className={`nav-item ${activeTab === 'human' ? 'active' : ''}`} onClick={() => setActiveTab('human')}>
            <Send size={20} /> Human Apply Queue
          </div>
          <div className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`} onClick={() => { setActiveTab('analytics'); fetchAnalytics(); }}>
            <BarChart2 size={20} /> Analytics
          </div>
          <div className={`nav-item ${activeTab === 'scope' ? 'active' : ''}`} onClick={() => setActiveTab('scope')}>
            <Target size={20} /> Application Scope
          </div>
          <div className={`nav-item ${activeTab === 'watchlist' ? 'active' : ''}`} onClick={() => setActiveTab('watchlist')}>
            <Eye size={20} /> Company Watchlist
          </div>
          <div className={`nav-item ${activeTab === 'config' ? 'active' : ''}`} onClick={() => setActiveTab('config')}>
            <Settings size={20} /> System Config
          </div>
          <div className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>
            <Settings size={20} /> Settings & Auth
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="main-content">
        {activeTab === 'home' && (
          <div className="fade-in">
            <h2>Command Center</h2>
            <p className="subtitle">Real-time telemetry of your autonomous application pipeline.</p>
            
            <div className="metrics-grid">
              <div className="glass-card">
                <div className="metric-label">Jobs Discovered</div>
                <div className="metric-value">{metrics?.total || 0}</div>
              </div>
              <div className="glass-card">
                <div className="metric-label">New Leads</div>
                <div className="metric-value">{metrics?.new || 0}</div>
              </div>
              <div className="glass-card">
                <div className="metric-label">Auto-Applied</div>
                <div className="metric-value">{metrics?.applied || 0}</div>
              </div>
              <div className="glass-card">
                <div className="metric-label">Interviews</div>
                <div className="metric-value">{metrics?.interviews || 0}</div>
              </div>
            </div>

            <div className="glass-card">
              <h3 style={{marginBottom: '1rem'}}>Pipeline Controls</h3>
              <p style={{color: 'var(--text-secondary)'}}>Manually trigger the background Python engines from the UI.</p>
              <div className="action-grid">
                <button className="btn" onClick={() => triggerAction('discover')}>
                  <Search size={18} /> Run Discovery
                </button>
                <button className="btn" onClick={() => triggerAction('apply')}>
                  <Send size={18} /> Auto-Apply
                </button>
                <button className="btn" onClick={() => triggerAction('track')}>
                  <Mail size={18} /> Sync Inbox
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'kb' && (
          <KnowledgeBaseEditor />
        )}

        {activeTab === 'onboarding' && (
          <Onboarding />
        )}

        {activeTab === 'portal' && (
          <div className="fade-in">
            <h2>Master Job Portal</h2>
            <p className="subtitle">Unified view of all discovered jobs and application statuses.</p>
            
            <div className="glass-card" style={{padding: 0}}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Job Title</th>
                    <th>Skill Gaps</th>
                    <th>Fit Score</th>
                    <th>Status</th>
                    <th>Link</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job, idx) => (
                    <tr key={idx}>
                      <td style={{fontWeight: 600}}>{job.company}</td>
                      <td>{job.title}</td>
                      <td>
                        {job.missing_skills ? (
                          <div style={{display: 'flex', flexWrap: 'wrap', gap: '4px'}}>
                            {job.missing_skills.split(',').map((skill, i) => (
                              <span key={i} style={{background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem', border: '1px solid rgba(239, 68, 68, 0.3)'}}>
                                {skill.trim()}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span style={{color: 'var(--text-secondary)', fontSize: '0.8rem'}}>-</span>
                        )}
                      </td>
                      <td>
                        <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                          <div style={{width: '100px', height: '6px', background: '#334155', borderRadius: '3px'}}>
                            <div style={{width: `${job.fit_score}%`, height: '100%', background: 'var(--accent)', borderRadius: '3px'}}></div>
                          </div>
                          <span>{job.fit_score}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${job.status}`}>{job.status.replace('_', ' ')}</span>
                        {job.scam_flags && (
                          <div style={{marginTop: '4px', fontSize: '0.7rem', color: '#fca5a5'}}>
                            ⚠️ Scam/Ghost: {job.scam_flags}
                          </div>
                        )}
                      </td>
                      <td><a href={job.url} target="_blank" rel="noreferrer" style={{color: 'var(--accent)'}}>View</a></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'manual' && (
          <div className="fade-in">
            <ManualReview />
          </div>
        )}

        {activeTab === 'human' && (
          <HumanApply token={token} />
        )}

        {activeTab === 'scope' && (
          <ApplicationScope />
        )}

        {activeTab === 'analytics' && (
          <div className="fade-in">
            <h2>Pipeline Analytics</h2>
            <p className="subtitle">Company friction rates and salary gap analysis from your application history.</p>

            <div className="glass-card" style={{marginBottom: '2rem'}}>
              <h3 style={{marginBottom: '1rem'}}>🚨 Company Friction Rate (Ghost / Rejection Rate)</h3>
              <p style={{color: 'var(--text-secondary)', marginBottom: '1rem'}}>Companies sorted by how often they reject or ghost applicants. 1.0 = always rejects/ghosts.</p>
              {frictionData.length === 0 ? (
                <p style={{color: 'var(--text-secondary)'}}>No data yet — apply to some jobs first.</p>
              ) : (
                <table className="data-table">
                  <thead><tr><th>Company</th><th>Total Apps</th><th>Rejected/Ghosted</th><th>Friction Rate</th></tr></thead>
                  <tbody>
                    {frictionData.map((r, i) => (
                      <tr key={i}>
                        <td style={{fontWeight: 600}}>{r.company}</td>
                        <td>{r.total}</td>
                        <td>{r.rejected}</td>
                        <td>
                          <span style={{color: r.friction_rate > 0.7 ? '#f87171' : r.friction_rate > 0.4 ? '#fbbf24' : '#4ade80', fontWeight: 700}}>
                            {(r.friction_rate * 100).toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="glass-card">
              <h3 style={{marginBottom: '1rem'}}>💰 Salary Gap Analysis</h3>
              {!salaryData ? (
                <p style={{color: 'var(--text-secondary)'}}>No salary data yet. Set a target salary in System Config and process some jobs.</p>
              ) : salaryData.error ? (
                <p style={{color: '#f87171'}}>{salaryData.error}</p>
              ) : (
                <div>
                  <div className="metrics-grid" style={{marginBottom: '1rem'}}>
                    <div className="glass-card"><div className="metric-label">Your Target</div><div className="metric-value" style={{fontSize: '1.5rem'}}>${salaryData.target_salary?.toLocaleString()}</div></div>
                    <div className="glass-card"><div className="metric-label">Market Average</div><div className="metric-value" style={{fontSize: '1.5rem'}}>${salaryData.market_average?.toLocaleString()}</div></div>
                    <div className="glass-card"><div className="metric-label">Macro Gap</div><div className="metric-value" style={{fontSize: '1.5rem', color: salaryData.macro_gap_percentage < 0 ? '#f87171' : '#4ade80'}}>{salaryData.macro_gap_percentage > 0 ? '+' : ''}{salaryData.macro_gap_percentage}%</div></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'config' && (
          <div className="fade-in">
            <h2>System Configuration</h2>
            <p className="subtitle">Tune the core SPrav MoE thresholds and System Prompts.</p>
            
            <div className="glass-card">
              <h3 style={{marginBottom: '1rem'}}>AI Decision Threshold</h3>
              <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem'}}>
                <div>
                  <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Minimum Fit Score (1.0 – 5.0 scale)</label>
                  <input type="number" step="0.1" min="1.0" max="5.0" value={sysConfig.threshold} onChange={e => setSysConfig({...sysConfig, threshold: parseFloat(e.target.value)})} style={{width: '100px', padding: '0.75rem', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff'}} />
                </div>
                <div>
                  <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Max Auto-Applies per Day</label>
                  <input type="number" value={sysConfig.max_applications_per_day || 30} onChange={e => setSysConfig({...sysConfig, max_applications_per_day: parseInt(e.target.value)})} style={{width: '100px', padding: '0.75rem', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff'}} />
                </div>
                <div>
                  <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Target Salary (e.g. $120,000)</label>
                  <input type="text" value={sysConfig.target_salary || ''} onChange={e => setSysConfig({...sysConfig, target_salary: e.target.value})} placeholder="$120,000" style={{width: '150px', padding: '0.75rem', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff'}} />
                </div>
              </div>

              <h3 style={{marginBottom: '1rem', marginTop: '2rem'}}>Phase 2: DeepSeek-R1 (Hard Logic Filter)</h3>
              <div style={{marginBottom: '1.5rem'}}>
                <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Filter System Prompt</label>
                <textarea rows="4" value={sysConfig.filter_prompt} onChange={e => setSysConfig({...sysConfig, filter_prompt: e.target.value})} style={{width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontFamily: 'monospace', fontSize: '0.9rem'}}></textarea>
                <small style={{color: 'var(--text-secondary)'}}>Use {'{threshold}'} to dynamically inject your fit score requirement.</small>
              </div>

              <h3 style={{marginBottom: '1rem', marginTop: '2rem'}}>Phase 3: Qwen2.5-Coder (ATS Resume Tailor)</h3>
              <div style={{marginBottom: '1.5rem'}}>
                <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Resume Tailoring System Prompt</label>
                <textarea rows="4" value={sysConfig.resume_prompt} onChange={e => setSysConfig({...sysConfig, resume_prompt: e.target.value})} style={{width: '100%', padding: '0.75rem', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontFamily: 'monospace', fontSize: '0.9rem'}}></textarea>
              </div>

              <button className="btn" onClick={saveConfig} style={{background: 'var(--success)', marginTop: '1rem'}}>💾 Save Configuration</button>
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <Settings token={token} />
        )}

        {activeTab === 'watchlist' && (
          <WatchlistManager token={token} />
        )}
      </div>

      <Copilot token={token} currentTab={activeTab} />
    </div>
  )
}

export default App
