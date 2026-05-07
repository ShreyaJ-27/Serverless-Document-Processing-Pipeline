import { useState, useEffect, useCallback, useMemo } from 'react'
import './index.css'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const FILE_ICONS = {
  pdf: '📄', txt: '📝', docx: '📋', doc: '📋',
  png: '🖼️', jpg: '🖼️', jpeg: '🖼️',
  default: '📁',
}

function fileIcon(filename = '') {
  const ext = filename.split('.').pop().toLowerCase()
  return FILE_ICONS[ext] || FILE_ICONS.default
}

function tagClass(tag) {
  const map = { invoice:'tag-invoice', contract:'tag-contract', hr:'tag-hr',
    finance:'tag-finance', legal:'tag-legal', report:'tag-report', memo:'tag-memo' }
  return map[tag.toLowerCase()] || 'tag-default'
}

function dtypeClass(t) {
  const map = { invoice:'dtype-invoice', contract:'dtype-contract', resume:'dtype-resume',
    receipt:'dtype-receipt', report:'dtype-report', memo:'dtype-memo' }
  return map[(t||'').toLowerCase()] || 'dtype-default'
}

function formatDate(d) {
  if (!d) return '—'
  const dt = typeof d === 'string' ? new Date(d) : d
  return dt.toLocaleString('en-US', { month:'short', day:'numeric', year:'numeric',
    hour:'2-digit', minute:'2-digit' })
}

// ── Sortable column header ───────────────────────────────────────────────────
function SortTh({ field, label, sortState, onSort }) {
  const active = sortState.field === field
  const icon = active ? (sortState.asc ? ' ↑' : ' ↓') : ' ↕'
  return (
    <th className={active ? 'active-sort' : ''} onClick={() => onSort(field)}>
      {label}<span className="sort-icon">{icon}</span>
    </th>
  )
}

// ── Toast ────────────────────────────────────────────────────────────────────
function Toast({ msg, type, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 3000); return () => clearTimeout(t) }, [onDone])
  return (
    <div className={`toast toast-${type}`}>
      {type === 'success' ? '✅' : '❌'} {msg}
    </div>
  )
}

// ── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [docs, setDocs]           = useState([])
  const [tags, setTags]           = useState([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)
  const [tagFilter, setTagFilter] = useState('')
  const [search, setSearch]       = useState('')
  const [spinning, setSpinning]   = useState(false)
  const [toast, setToast]         = useState(null)
  const [sort, setSort]           = useState({ field: 'processing_date', asc: false })

  const fetchTags = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/tags`)
      if (r.ok) { const d = await r.json(); setTags(d.tags || []) }
    } catch { /* non-fatal */ }
  }, [])

  const fetchDocs = useCallback(async (tag = tagFilter) => {
    setLoading(true); setError(null); setSpinning(true)
    try {
      const url = `${API_BASE}/documents${tag ? `?tag=${encodeURIComponent(tag)}` : ''}`
      const r = await fetch(url)
      if (!r.ok) throw new Error(`Server returned ${r.status}`)
      const data = await r.json()
      setDocs(data.documents || [])
      setToast({ msg: `Loaded ${data.count} document${data.count !== 1 ? 's' : ''}`, type: 'success' })
    } catch (e) {
      setError(e.message)
      setToast({ msg: 'Failed to load documents', type: 'error' })
    } finally { setLoading(false); setSpinning(false) }
  }, [tagFilter])

  useEffect(() => { fetchDocs(); fetchTags() }, [])

  const handleTagChange = (e) => { setTagFilter(e.target.value); fetchDocs(e.target.value) }
  const handleSort = (field) => {
    setSort(s => s.field === field ? { field, asc: !s.asc } : { field, asc: true })
  }

  const maxWords = useMemo(() => Math.max(1, ...docs.map(d => d.word_count || 0)), [docs])

  const filtered = useMemo(() => {
    let out = docs
    if (search.trim()) {
      const q = search.toLowerCase()
      out = out.filter(d =>
        d.filename?.toLowerCase().includes(q) ||
        d.tags?.toLowerCase().includes(q) ||
        d.document_type?.toLowerCase().includes(q) ||
        d.summary?.toLowerCase().includes(q)
      )
    }
    out = [...out].sort((a, b) => {
      let va = a[sort.field] ?? '', vb = b[sort.field] ?? ''
      if (typeof va === 'number') return sort.asc ? va - vb : vb - va
      va = String(va).toLowerCase(); vb = String(vb).toLowerCase()
      return sort.asc ? va.localeCompare(vb) : vb.localeCompare(va)
    })
    return out
  }, [docs, search, sort])

  // ── Stats ──────────────────────────────────────────────────────────────────
  const totalWords    = docs.reduce((s, d) => s + (d.word_count || 0), 0)
  const uniqueLangs   = new Set(docs.map(d => d.language).filter(Boolean)).size
  const uniqueTypes   = new Set(docs.map(d => d.document_type).filter(Boolean)).size

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-brand">
          <div className="header-icon">🔬</div>
          <div>
            <div className="header-title">DocProcessor</div>
            <div className="header-subtitle">Serverless document intelligence pipeline</div>
          </div>
        </div>
        <div className="header-badge">● LIVE</div>
      </header>

      <main className="main-content">
        {/* ── Stats row ── */}
        <div className="stats-row">
          <div className="stat-card">
            <div className="stat-label">Total Documents</div>
            <div className="stat-value">{docs.length}</div>
            <div className="stat-icon">📂</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Words Processed</div>
            <div className="stat-value">{totalWords.toLocaleString()}</div>
            <div className="stat-icon">📝</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Languages</div>
            <div className="stat-value">{uniqueLangs}</div>
            <div className="stat-icon">🌍</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Document Types</div>
            <div className="stat-value">{uniqueTypes}</div>
            <div className="stat-icon">🗂️</div>
          </div>
        </div>

        {/* ── Controls ── */}
        <div className="controls">
          <div className="search-wrap">
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
            </svg>
            <input
              id="search-input"
              className="search-input"
              placeholder="Search filename, tags, type, summary…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          <select id="tag-filter" className="tag-select" value={tagFilter} onChange={handleTagChange}>
            <option value="">All Tags</option>
            {tags.map(t => <option key={t} value={t}>{t}</option>)}
          </select>

          <button
            id="refresh-btn"
            className={`refresh-btn${spinning ? ' spinning' : ''}`}
            onClick={() => fetchDocs()}
          >
            <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Refresh
          </button>
        </div>

        {/* ── Table ── */}
        <div className="table-card">
          <div className="table-header-bar">
            <span className="table-title">Processed Documents</span>
            <span className="table-count">{filtered.length} of {docs.length}</span>
          </div>

          <div className="table-wrap">
            {loading ? (
              <div className="state-box"><div className="spinner"/><div className="state-title">Loading documents…</div></div>
            ) : error ? (
              <div className="state-box error-box">
                <div className="state-icon">⚠️</div>
                <div className="state-title">Could not load data</div>
                <div className="state-sub">{error}</div>
              </div>
            ) : filtered.length === 0 ? (
              <div className="state-box">
                <div className="state-icon">🔍</div>
                <div className="state-title">No documents found</div>
                <div className="state-sub">Try a different search or upload files to the GCS bucket.</div>
              </div>
            ) : (
              <table id="documents-table">
                <thead>
                  <tr>
                    <SortTh field="filename"         label="Filename"      sortState={sort} onSort={handleSort}/>
                    <SortTh field="processing_date"  label="Processed"     sortState={sort} onSort={handleSort}/>
                    <SortTh field="document_type"    label="Type"          sortState={sort} onSort={handleSort}/>
                    <SortTh field="tags"             label="Tags"          sortState={sort} onSort={handleSort}/>
                    <SortTh field="word_count"       label="Words"         sortState={sort} onSort={handleSort}/>
                    <SortTh field="language"         label="Lang"          sortState={sort} onSort={handleSort}/>
                    <th>Summary</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((doc, i) => (
                    <tr key={`${doc.filename}-${i}`} style={{ animationDelay: `${i * 40}ms` }}>
                      <td>
                        <div className="td-filename">
                          <span className="file-icon">{fileIcon(doc.filename)}</span>
                          {doc.filename}
                        </div>
                      </td>
                      <td className="td-date">{formatDate(doc.processing_date)}</td>
                      <td>
                        <span className={`dtype-badge ${dtypeClass(doc.document_type)}`}>
                          {doc.document_type || '—'}
                        </span>
                      </td>
                      <td>
                        <div className="tag-list">
                          {(doc.tags || '').split(',').filter(Boolean).map(tag => (
                            <span
                              key={tag}
                              className={`tag ${tagClass(tag.trim())}`}
                              onClick={() => { setTagFilter(tag.trim()); fetchDocs(tag.trim()) }}
                              title={`Filter by "${tag.trim()}"`}
                            >
                              {tag.trim()}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <div className="word-wrap">
                          <div className="word-bar">
                            <div className="word-fill" style={{ width: `${Math.min(100, (doc.word_count / maxWords) * 100)}%` }}/>
                          </div>
                          <span className="word-count-num">{(doc.word_count || 0).toLocaleString()}</span>
                        </div>
                      </td>
                      <td><span className="lang-pill">{doc.language || 'en'}</span></td>
                      <td className="summary-cell">
                        <div className="summary-text" title={doc.summary}>{doc.summary || '—'}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>

      {toast && (
        <Toast msg={toast.msg} type={toast.type} onDone={() => setToast(null)}/>
      )}
    </div>
  )
}
