import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Target, Plus, Trash2, Save, MapPin, Briefcase, Clock, Award, Wifi } from 'lucide-react'
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
        <button className={`btn save-btn ${saved ? 'saved' : ''}`} onClick={save} disabled={saving}>
          {saving ? 'Saving…' : saved ? '✓ Saved' : <><Save size={16} /> Save Scope</>}
        </button>
      </div>

      {error && <div className="scope-error">{error}</div>}

      <div className="scope-grid">

        {/* ── Work Mode ─────────────────────────────────────────────────── */}
        <div className="premium-card scope-card">
          <h3><Wifi size={18} /> Work Mode</h3>
          <p className="card-hint">Controls remote vs on-site filtering across all jobs.</p>
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
          <h3><Award size={18} /> Experience Level</h3>
          <p className="card-hint">Filters by seniority signals found in the job title and description.</p>
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
          <h3><MapPin size={18} /> Locations</h3>
          <p className="card-hint">
            Add cities, countries, or "Remote". Tag each as <em>Apply</em> (prefer),
            <em>Exclude</em> (hard block), or <em>No Preference</em> (pass-through).
            Only "Exclude" tags actually filter — "Apply" is a soft preference signal.
          </p>

          <div className="tag-input-row">
            <input
              ref={locInputRef}
              type="text"
              placeholder="City, Country, or 'Remote'…"
              onKeyDown={e => e.key === 'Enter' && addLocation()}
            />
            <button className="btn-icon" onClick={addLocation}><Plus size={14} /> Add</button>
          </div>

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
          <h3><Briefcase size={18} /> Job Roles / Titles</h3>
          <p className="card-hint">
            Keywords are matched against the extracted job title using fuzzy matching
            (not exact string). "Exclude" is a hard block; "Apply" is a soft preference.
          </p>

          <div className="tag-input-row">
            <input
              ref={roleInputRef}
              type="text"
              placeholder="e.g. Backend Engineer, Data Analyst…"
              onKeyDown={e => e.key === 'Enter' && addRole()}
            />
            <button className="btn-icon" onClick={addRole}><Plus size={14} /> Add</button>
          </div>

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
