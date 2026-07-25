import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Target, Plus, Trash2, Save, MapPin, Briefcase, Clock, Award, Wifi, Sparkles } from 'lucide-react'
import './ApplicationScope.css'

const API_BASE = 'http://localhost:8000/api'

const PREF_OPTIONS = ['apply', 'exclude', 'no_preference']
const PREF_LABEL   = { apply: 'Apply', exclude: 'Exclude', no_preference: 'No Preference' }

const JOB_TYPE_KEYS = ['full_time', 'part_time', 'internship', 'contract', 'freelance']
const JOB_TYPE_LABEL = {
  full_time: 'Full-time',
  part_time: 'Part-time',
  internship: 'Internship',
  contract: 'Contract',
  freelance: 'Freelance',
}

const WORK_MODE_OPTIONS = [
  { value: 'remote_only',      label: 'Remote Only' },
  { value: 'remote_preferred', label: 'Remote + On-site' },
  { value: 'onsite_only',      label: 'On-site Only' },
  { value: 'any',              label: 'No Preference' },
]

const EXP_OPTIONS = [
  { value: 'any',    label: 'No Preference' },
  { value: 'entry',  label: 'Entry-level' },
  { value: 'mid',    label: 'Mid-level' },
  { value: 'senior', label: 'Senior' },
]

const DEFAULT_SCOPE = {
  locations: [],
  work_mode: 'any',
  roles: [],
  job_types: { full_time: 'include', part_time: 'include', internship: 'include', contract: 'include', freelance: 'include' },
  experience_level: 'any',
}

export default function ApplicationScope() {
  const [scope, setScope]     = useState(DEFAULT_SCOPE)
  const [saved, setSaved]     = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving]   = useState(false)
  const [detecting, setDetecting] = useState(false)
  const [error, setError]     = useState('')

  // New-tag input refs
  const locInputRef  = useRef(null)
  const roleInputRef = useRef(null)

  useEffect(() => {
    axios.get(`${API_BASE}/scope`)
      .then(r => { setScope({ ...DEFAULT_SCOPE, ...r.data }); setLoading(false) })
      .catch(() => { setLoading(false); setError('Could not load scope config from backend.') })
  }, [])

  const save = async () => {
    setSaving(true)
    setSaved(false)
    try {
      await axios.post(`${API_BASE}/scope`, scope)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e) {
      setError('Save failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setSaving(false)
    }
  }

  const [suggestedRoles, setSuggestedRoles] = useState([]);
  const [suggestedLocs, setSuggestedLocs] = useState([]);

  const autoDetectScope = async () => {
    setDetecting(true);
    setError('');
    try {
      const payload = {
        current_roles: scope.roles.map(r => r.keyword),
        current_locations: scope.locations.map(l => l.label)
      };
      const res = await axios.post(`${API_BASE}/scope/suggest`, payload);
      if (res.data.status === "success" && res.data.data) {
        setSuggestedRoles(prev => Array.from(new Set([...prev, ...(res.data.data.roles || [])])));
        setSuggestedLocs(prev => Array.from(new Set([...prev, ...(res.data.data.locations || [])])));
      } else {
        setError(res.data.message || 'Failed to generate suggestions.');
      }
    } catch (e) {
      setError('Auto-detect failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setDetecting(false);
    }
  }

  const addSuggestedRole = (r) => {
    if (!scope.roles.some(x => x.keyword.toLowerCase() === r.toLowerCase())) {
      setScope(s => ({ ...s, roles: [...s.roles, { keyword: r, preference: 'apply' }] }));
    }
    setSuggestedRoles(prev => prev.filter(x => x !== r));
  };

  const addSuggestedLoc = (l) => {
    if (!scope.locations.some(x => x.label.toLowerCase() === l.toLowerCase())) {
      setScope(s => ({ ...s, locations: [...s.locations, { label: l, preference: 'apply' }] }));
    }
    setSuggestedLocs(prev => prev.filter(x => x !== l));
  };

  // ── Locations ─────────────────────────────────────────────────────────────
  const addLocation = () => {
    const val = locInputRef.current?.value?.trim()
    if (!val) return
    setScope(s => ({ ...s, locations: [...s.locations, { label: val, preference: 'apply' }] }))
    locInputRef.current.value = ''
  }

  const updateLocPref = (i, pref) =>
    setScope(s => ({ ...s, locations: s.locations.map((l, idx) => idx === i ? { ...l, preference: pref } : l) }))

  const removeLocation = i =>
    setScope(s => ({ ...s, locations: s.locations.filter((_, idx) => idx !== i) }))

  // ── Roles ─────────────────────────────────────────────────────────────────
  const addRole = () => {
    const val = roleInputRef.current?.value?.trim()
    if (!val) return
    setScope(s => ({ ...s, roles: [...s.roles, { keyword: val, preference: 'apply' }] }))
    roleInputRef.current.value = ''
  }

  const updateRolePref = (i, pref) =>
    setScope(s => ({ ...s, roles: s.roles.map((r, idx) => idx === i ? { ...r, preference: pref } : r) }))

  const removeRole = i =>
    setScope(s => ({ ...s, roles: s.roles.filter((_, idx) => idx !== i) }))

  // ── Job types ─────────────────────────────────────────────────────────────
  const toggleJobType = (key) =>
    setScope(s => ({
      ...s,
      job_types: {
        ...s.job_types,
        [key]: s.job_types[key] === 'include' ? 'exclude' : 'include'
      }
    }))

  if (loading) return <div className="scope-loading">Loading scope config…</div>

  return (
    <div className="scope-container fade-in">
      <div className="scope-header">
        <div>
          <h2><Target size={22} /> Application Scope</h2>
          <p className="subtitle">
            Define exactly what the AI is allowed to apply to. Hard "Exclude" rules
            reject jobs before any LLM inference runs — saving compute and your application
            reputation. Changes take effect on the next discovery cycle (no restart needed).
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className={`btn save-btn ${saved ? 'saved' : ''}`} onClick={save} disabled={saving}>
            {saving ? 'Saving…' : saved ? '✓ Saved' : <><Save size={16} /> Save Scope</>}
          </button>
        </div>
      </div>

      {error && <div className="scope-error">{error}</div>}

      <div className="scope-grid">

        {/* ── Work Mode ─────────────────────────────────────────────────── */}
        <div className="premium-card scope-card">
          <h3><Wifi size={18} /> What is your preferred Work Mode?</h3>
          <p className="card-hint">Controls remote vs on-site filtering. The AI will instantly reject jobs that do not match your requirement.</p>
          <div className="seg-control">
            {WORK_MODE_OPTIONS.map(opt => (
              <button
                key={opt.value}
                className={`seg-btn ${scope.work_mode === opt.value ? 'active' : ''}`}
                onClick={() => setScope(s => ({ ...s, work_mode: opt.value }))}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Experience Level ──────────────────────────────────────────── */}
        <div className="premium-card scope-card">
          <h3><Award size={18} /> What is your target Experience Level?</h3>
          <p className="card-hint">Filters by seniority. If you select "Mid", the AI will block "Staff" or "Principal" roles.</p>
          <div className="seg-control">
            {EXP_OPTIONS.map(opt => (
              <button
                key={opt.value}
                className={`seg-btn ${scope.experience_level === opt.value ? 'active' : ''}`}
                onClick={() => setScope(s => ({ ...s, experience_level: opt.value }))}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Locations ──────────────────────────────────────────────────── */}
        <div className="premium-card scope-card full-width">
          <h3><MapPin size={18} /> Are you willing to relocate? Which locations do you target?</h3>
          <p className="card-hint">
            Add target cities or countries. Tag as <em>Apply</em> (preferred) or 
            <em>Exclude</em> (hard block—do not apply here).
          </p>

          <div className="tag-input-row">
            <input ref={locInputRef} type="text" list="popular-locations" placeholder="City, Country, or 'Remote'..." onKeyDown={e => e.key === 'Enter' && addLocation()} />
            <datalist id="popular-locations">
              <option value="Pune, Maharashtra, India" />
              <option value="Bangalore, Karnataka, India" />
              <option value="Hyderabad, Telangana, India" />
              <option value="Mumbai, Maharashtra, India" />
              <option value="Delhi NCR, India" />
              <option value="Chennai, Tamil Nadu, India" />
              <option value="Remote India" />
              <option value="San Francisco, CA, USA" />
              <option value="New York, NY, USA" />
              <option value="Seattle, WA, USA" />
              <option value="Austin, TX, USA" />
              <option value="London, UK" />
              <option value="Toronto, ON, Canada" />
              <option value="Remote Global" />
            </datalist>
            <button className="btn-icon" onClick={addLocation}><Plus size={14} /> Add</button>
          </div>
            
          <div style={{ marginBottom: '1rem' }}>
            <button className="btn" onClick={autoDetectScope} disabled={detecting} style={{ background: 'rgba(79, 70, 229, 0.1)', color: 'var(--accent)', border: '1px solid rgba(79, 70, 229, 0.3)', width: 'fit-content' }}>
              {detecting ? 'Analyzing...' : <><Sparkles size={14} /> AI: Suggest More Locations</>}
            </button>
          </div>

          {suggestedLocs.length > 0 && (
            <div style={{ marginBottom: '1rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
              <Sparkles size={14} color="var(--accent)" /> <span style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>AI Suggestions:</span>
              {suggestedLocs.map(l => (
                <button key={l} onClick={() => addSuggestedLoc(l)} style={{ background: 'var(--bg-surface)', border: '1px solid var(--accent)', color: 'var(--accent)', padding: '0.3rem 0.6rem', borderRadius: '12px', fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  {l} <Plus size={12} />
                </button>
              ))}
            </div>
          )}

          <div className="tag-list">
            {scope.locations.length === 0 && (
              <p className="empty-hint">No locations added yet — all locations pass through.</p>
            )}
            {scope.locations.map((loc, i) => (
              <div key={i} className="tag-row">
                <span className="tag-label"><MapPin size={12} /> {loc.label}</span>
                <div className="pref-seg">
                  {PREF_OPTIONS.map(p => (
                    <button
                      key={p}
                      className={`pref-btn ${loc.preference === p ? `active pref-${p}` : ''}`}
                      onClick={() => updateLocPref(i, p)}
                    >
                      {PREF_LABEL[p]}
                    </button>
                  ))}
                </div>
                <button className="btn-icon danger" onClick={() => removeLocation(i)}><Trash2 size={13} /></button>
              </div>
            ))}
          </div>
        </div>

        {/* ── Roles / Titles ─────────────────────────────────────────────── */}
        <div className="premium-card scope-card full-width">
          <h3><Briefcase size={18} /> Which Job Roles are you looking for?</h3>
          <p className="card-hint">
            Enter target titles (e.g., "Backend Engineer"). The AI will fuzzy-match these against job titles. 
            You can also Exclude titles you explicitly do not want.
          </p>

          <div className="tag-input-row">
            <input ref={roleInputRef} type="text" placeholder="e.g. Backend Engineer, Data Analyst..." onKeyDown={e => e.key === 'Enter' && addRole()} />
            <button className="btn-icon" onClick={addRole}><Plus size={14} /> Add</button>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <button className="btn" onClick={autoDetectScope} disabled={detecting} style={{ background: 'rgba(79, 70, 229, 0.1)', color: 'var(--accent)', border: '1px solid rgba(79, 70, 229, 0.3)', width: 'fit-content' }}>
              {detecting ? 'Analyzing...' : <><Sparkles size={14} /> AI: Suggest More Roles</>}
            </button>
          </div>

          {suggestedRoles.length > 0 && (
            <div style={{ marginBottom: '1rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
              <Sparkles size={14} color="var(--accent)" /> <span style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>AI Suggestions:</span>
              {suggestedRoles.map(r => (
                <button key={r} onClick={() => addSuggestedRole(r)} style={{ background: 'var(--bg-surface)', border: '1px solid var(--accent)', color: 'var(--accent)', padding: '0.3rem 0.6rem', borderRadius: '12px', fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  {r} <Plus size={12} />
                </button>
              ))}
            </div>
          )}

          <div className="tag-list">
            {scope.roles.length === 0 && (
              <p className="empty-hint">No role filters — all job titles pass through.</p>
            )}
            {scope.roles.map((role, i) => (
              <div key={i} className="tag-row">
                <span className="tag-label"><Briefcase size={12} /> {role.keyword}</span>
                <div className="pref-seg">
                  {PREF_OPTIONS.map(p => (
                    <button
                      key={p}
                      className={`pref-btn ${role.preference === p ? `active pref-${p}` : ''}`}
                      onClick={() => updateRolePref(i, p)}
                    >
                      {PREF_LABEL[p]}
                    </button>
                  ))}
                </div>
                <button className="btn-icon danger" onClick={() => removeRole(i)}><Trash2 size={13} /></button>
              </div>
            ))}
          </div>
        </div>

        {/* ── Job Type ───────────────────────────────────────────────────── */}
        <div className="premium-card scope-card full-width">
          <h3><Clock size={18} /> Job Type</h3>
          <p className="card-hint">
            Toggle each type. "Included" types pass through; "Excluded" types are hard-blocked
            before any LLM inference runs.
          </p>
          <div className="jobtype-grid">
            {JOB_TYPE_KEYS.map(key => {
              const isIncluded = scope.job_types?.[key] !== 'exclude'
              return (
                <div
                  key={key}
                  className={`jobtype-tile ${isIncluded ? 'included' : 'excluded'}`}
                  onClick={() => toggleJobType(key)}
                >
                  <div className="jobtype-label">{JOB_TYPE_LABEL[key]}</div>
                  <div className={`jobtype-badge ${isIncluded ? 'badge-include' : 'badge-exclude'}`}>
                    {isIncluded ? 'Include' : 'Exclude'}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

      </div>

      <div className="scope-footer">
        <button className={`btn save-btn ${saved ? 'saved' : ''}`} onClick={save} disabled={saving}>
          {saving ? 'Saving…' : saved ? '✓ Scope Saved!' : <><Save size={16} /> Save Scope</>}
        </button>
        <span className="footer-hint">
          Scope rules are enforced before Phase 2 — excluded jobs are marked
          <code>out_of_scope</code> in the Job Portal with the exact reason.
        </span>
      </div>
    </div>
  )
}
