import { useState, useEffect } from 'react'
import axios from 'axios'
import { Briefcase, LayoutDashboard, Database, Activity, Search, Send, Mail, CheckCircle, Settings as SettingsIcon, BarChart2, Target, Eye, Sun, Moon } from 'lucide-react'
import ManualReview from './pages/ManualReview'
import KnowledgeBaseEditor from './pages/KnowledgeBaseEditor'
import Onboarding from './pages/Onboarding'
import ApplicationScope from './pages/ApplicationScope'
import WatchlistManager from './pages/WatchlistManager'
import SettingsPage from './pages/Settings'
import AuthGate from './AuthGate'
import HumanApply from './HumanApply'
import Copilot from './Copilot'
import JobDetailsModal from './JobDetailsModal'
import './index.css'

const API_BASE = '/api'

function App() {
  const [activeTab, setActiveTab] = useState('home')
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark')
  const [metrics, setMetrics] = useState(null)
  const [jobs, setJobs] = useState([])
  const [sysConfig, setSysConfig] = useState({threshold: 4.0, filter_prompt: "", resume_prompt: "", max_applications_per_day_total: 150, max_applications_per_day_per_portal: 25, max_applications_per_day_per_company: 5, target_salary: ""})
  const [frictionData, setFrictionData] = useState([])
  const [salaryData, setSalaryData] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('sprav_token') || null)
  const [selectedJobId, setSelectedJobId] = useState(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    const initializeAuth = async (retries = 5) => {
      if (!token) {
        try {
          const res = await axios.get(`${API_BASE}/auto-login`);
          if (res.data.access_token) {
            setToken(res.data.access_token);
            if (res.data.recovery_key) {
              alert(`Master Recovery Key Generated: ${res.data.recovery_key}\nSave this if you ever need to recover your encrypted database on another machine!`);
            }
          }
        } catch (e) {
          console.error(`Auto-login failed. Retries left: ${retries}`, e);
          if (retries > 0) {
            setTimeout(() => initializeAuth(retries - 1), 1000); // Retry after 1 second
          } else {
            alert("Failed to connect to SPrav Engine. Please restart the application.");
          }
        }
      }
    };
    initializeAuth();
  }, []);

  useEffect(() => {
    if (token) {
      localStorage.setItem('sprav_token', token)
      
      const reqInterceptor = axios.interceptors.request.use(config => {
        config.headers.Authorization = `Bearer ${token}`
        return config
      })

      const resInterceptor = axios.interceptors.response.use(
        response => response,
        error => {
          if (error.response && error.response.status === 401) {
            localStorage.removeItem('sprav_token');
            setToken(null);
          }
          return Promise.reject(error);
        }
      )

      fetchMetrics()
      fetchJobs()
      fetchConfig()
      
      const intervalId = setInterval(() => {
          fetchMetrics()
          fetchJobs()
      }, 5000)

      return () => {
        clearInterval(intervalId)
        axios.interceptors.request.eject(reqInterceptor);
        axios.interceptors.response.eject(resInterceptor);
      }
    }
  }, [token])

  if (!token) {
    return (
        <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: 'var(--bg-base)' }}>
            <div className="loading-spinner"></div>
            <p style={{marginLeft: '1rem', color: 'var(--text-secondary)'}}>Initializing Local Desktop Session...</p>
        </div>
    );
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

  const handleWipeDatabase = async () => {
    if (window.confirm("WARNING: This will permanently delete ALL scraped jobs, your application history, and reset your analytics to zero. Are you absolutely sure?")) {
      try {
        await axios.post(`${API_BASE}/debug/reset-jobs`)
        alert("Database wiped successfully. You now have a clean slate.")
        fetchJobs()
        fetchAnalytics()
      } catch (e) {
        console.error(e)
        alert("Failed to wipe database.")
      }
    }
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
      if (action === 'apply') {
        alert("Auto-Apply is continuously running in the background via the LangGraph daemon! You can watch the Job Portal tab to see the live updates.")
      } else {
        alert(`Triggered ${action} in background! The dashboard will update automatically.`)
      }
    } catch (e) {
      console.error(e)
    }
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
          <div className={`nav-item ${activeTab === 'human' ? 'active' : ''}`} onClick={() => setActiveTab('human')}>
            <CheckCircle size={20} /> Action Required
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
            <SettingsIcon size={20} /> System Config
          </div>
          <div className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>
            <SettingsIcon size={20} /> Settings &amp; Auth
          </div>
          
          <div style={{ marginTop: 'auto', paddingTop: '1rem' }}>
            <div className="nav-item" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
              {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
            </div>
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
              <div className="premium-card">
                <div className="metric-label">Jobs Discovered</div>
                <div className="metric-value">{metrics?.total || 0}</div>
              </div>
              <div className="premium-card">
                <div className="metric-label">New Leads</div>
                <div className="metric-value">{metrics?.new || 0}</div>
              </div>
              <div className="premium-card">
                <div className="metric-label">Auto-Applied</div>
                <div className="metric-value">{metrics?.applied || 0}</div>
              </div>
              <div className="premium-card">
                <div className="metric-label">Interviews</div>
                <div className="metric-value">{metrics?.interviews || 0}</div>
              </div>
            </div>

            <div className="premium-card">
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
            
            <div className="premium-card" style={{padding: 0}}>
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
                      <td>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                          <a href={job.url} target="_blank" rel="noreferrer" style={{color: 'var(--text-secondary)'}}>View</a>
                          <button className="btn" onClick={() => setSelectedJobId(job.id)} style={{ padding: '4px 8px', fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)' }}>Audit Log</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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

            <div className="premium-card" style={{marginBottom: '2rem'}}>
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

            <div className="premium-card">
              <h3 style={{marginBottom: '1rem'}}>💰 Salary Gap Analysis</h3>
              {!salaryData ? (
                <p style={{color: 'var(--text-secondary)'}}>No salary data yet. Set a target salary in System Config and process some jobs.</p>
              ) : salaryData.error ? (
                <p style={{color: '#f87171'}}>{salaryData.error}</p>
              ) : (
                <div>
                  <div className="metrics-grid" style={{marginBottom: '1rem'}}>
                    <div className="premium-card"><div className="metric-label">Your Target</div><div className="metric-value" style={{fontSize: '1.5rem'}}>{salaryData.target_salary ? `$${salaryData.target_salary.toLocaleString()}` : <span style={{color: 'var(--text-secondary)'}}>Not Set</span>}</div></div>
                    <div className="premium-card"><div className="metric-label">Market Average</div><div className="metric-value" style={{fontSize: '1.5rem'}}>${salaryData.market_average?.toLocaleString()}</div></div>
                    <div className="premium-card"><div className="metric-label">Macro Gap</div><div className="metric-value" style={{fontSize: '1.5rem', color: salaryData.target_salary ? (salaryData.macro_gap_percentage < 0 ? '#f87171' : '#4ade80') : 'var(--text-secondary)'}}>{salaryData.target_salary ? `${salaryData.macro_gap_percentage > 0 ? '+' : ''}${salaryData.macro_gap_percentage}%` : 'N/A'}</div></div>
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
            
            <div className="premium-card">
              <h3 style={{marginBottom: '1rem'}}>AI Decision Threshold</h3>
              <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem'}}>
                <div>
                  <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Minimum Fit Score (1.0 – 5.0 scale)</label>
                  <input type="number" step="0.1" min="1.0" max="5.0" value={sysConfig.threshold} onChange={e => setSysConfig({...sysConfig, threshold: parseFloat(e.target.value)})} style={{width: '100px', padding: '0.75rem', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff'}} />
                </div>
                <div>
                  <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Max Auto-Applies per Company</label>
                  <input type="number" value={sysConfig.max_applications_per_day_per_company || 5} onChange={e => setSysConfig({...sysConfig, max_applications_per_day_per_company: parseInt(e.target.value)})} style={{width: '100px', padding: '0.75rem', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff'}} />
                </div>
                <div>
                  <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Max Auto-Applies per Portal</label>
                  <input type="number" value={sysConfig.max_applications_per_day_per_portal || 25} onChange={e => setSysConfig({...sysConfig, max_applications_per_day_per_portal: parseInt(e.target.value)})} style={{width: '100px', padding: '0.75rem', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff'}} />
                </div>
                <div>
                  <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Max Auto-Applies Total</label>
                  <input type="number" value={sysConfig.max_applications_per_day_total || 150} onChange={e => setSysConfig({...sysConfig, max_applications_per_day_total: parseInt(e.target.value)})} style={{width: '100px', padding: '0.75rem', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff'}} />
                </div>
                <div>
                  <label style={{display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)'}}>Target Salary (Optional)</label>
                  <input type="text" value={sysConfig.target_salary || ''} onChange={e => setSysConfig({...sysConfig, target_salary: e.target.value})} placeholder="e.g. $120,000" style={{width: '150px', padding: '0.75rem', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff'}} />
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
            
            <div className="premium-card" style={{marginTop: '2rem', border: '1px solid rgba(239, 68, 68, 0.3)'}}>
              <h3 style={{marginBottom: '1rem', color: '#fca5a5'}}>Danger Zone</h3>
              <p style={{color: 'var(--text-secondary)', marginBottom: '1.5rem'}}>
                If the background AI started scraping jobs before you finished setting up your Knowledge Base, you might have a lot of irrelevant or low-score jobs in your portal. Click the button below to wipe all jobs and analytics clean, giving you a fresh start.
              </p>
              <button className="btn" onClick={handleWipeDatabase} style={{background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', border: '1px solid rgba(239, 68, 68, 0.3)'}}>
                🗑️ Wipe Job Database
              </button>
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <SettingsPage token={token} />
        )}

        {activeTab === 'watchlist' && (
          <WatchlistManager token={token} />
        )}
      </div>

      <Copilot token={token} currentTab={activeTab} />

      {selectedJobId && (
        <JobDetailsModal 
          jobId={selectedJobId} 
          token={token} 
          onClose={() => setSelectedJobId(null)} 
        />
      )}
    </div>
  )
}

export default App
