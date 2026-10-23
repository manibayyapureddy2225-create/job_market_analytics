import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [jobs, setJobs] = useState([])
  const [search, setSearch] = useState('')
  const [location, setLocation] = useState('')
  const [remoteType, setRemoteType] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Tracker state variables
  const [savedIds, setSavedIds] = useState([])
  const [trackerOpen, setTrackerOpen] = useState(false)
  const [applications, setApplications] = useState([])
  const [notice, setNotice] = useState('')

  // Load applications on initial mount to pre-populate saved states
  useEffect(() => {
    loadApplications()
  }, [])

  // Load jobs based on filters
  useEffect(() => {
    const controller = new AbortController()

    async function loadJobs() {
      setLoading(true)
      setError('')

      try {
        const params = new URLSearchParams({
          search,
          location,
          remote_type: remoteType,
          limit: '100',
        })

        const response = await fetch(`/api/jobs?${params}`, {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error('Unable to load jobs. Check the backend.')
        }

        const data = await response.json()
        setJobs(data.jobs || [])
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Something went wrong.')
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }

    loadJobs()
    return () => controller.abort()
  }, [search, location, remoteType])

  // Application tracker functions
  async function loadApplications() {
    try {
      const response = await fetch('/api/applications')
      if (!response.ok) throw new Error('Could not load saved jobs')

      const data = await response.json()
      setApplications(data)
      setSavedIds(data.map((application) => application.job_id))
    } catch (err) {
      console.error(err.message)
    }
  }

  async function saveJob(jobId) {
    try {
      const response = await fetch(`/api/applications/${jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: 'Saved',
          notes: '',
          application_date: null,
        }),
      })

      if (!response.ok) throw new Error('Could not save this job')

      await loadApplications()
      setNotice('Job saved successfully!')
    } catch (err) {
      setNotice(err.message)
    }
  }

  async function updateApplication(jobId, status) {
    try {
      const current = applications.find((item) => item.job_id === jobId)

      const response = await fetch(`/api/applications/${jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status,
          notes: current?.notes || '',
          application_date: current?.application_date || null,
        }),
      })

      if (!response.ok) throw new Error('Could not update application')

      await loadApplications()
      setNotice('Application status updated!')
    } catch (err) {
      setNotice(err.message)
    }
  }

  async function deleteApplication(jobId) {
    try {
      const response = await fetch(`/api/applications/${jobId}`, {
        method: 'DELETE',
      })

      if (!response.ok) throw new Error('Could not remove saved job')

      await loadApplications()
      setNotice('Job removed from tracker.')
    } catch (err) {
      setNotice(err.message)
    }
  }

  return (
    <div className="app">
      <header className="hero">
        <div className="brand">JOB MARKET ANALYTICS</div>
        <h1>Find your next opportunity.</h1>
        <p>Explore job openings, discover employers, and track market opportunities.</p>
        <div className="hero-stats">
          <div>
            <strong>{jobs.length}</strong>
            <span>Jobs displayed</span>
          </div>
          <div>
            <strong>3</strong>
            <span>Data sources</span>
          </div>
          <div>
            <strong>SQL + Python</strong>
            <span>Analytics engine</span>
          </div>
        </div>
      </header>

      <main className="content">
        {/* Application Tracker Toolbar */}
        <div className="tracker-toolbar">
          <button
            className="tracker-button"
            onClick={async () => {
              try {
                await loadApplications()
                setTrackerOpen(!trackerOpen)
              } catch (err) {
                setNotice(err.message)
              }
            }}
          >
            📋 Application Tracker ({savedIds.length})
          </button>
          {notice && <p role="status">{notice}</p>}
        </div>

        {/* Tracker Panel Dropdown / Toggle */}
        {trackerOpen && (
          <section className="tracker-panel">
            <h2>My Application Tracker</h2>
            {applications.length === 0 ? (
              <p>No saved jobs yet. Save a job to get started.</p>
            ) : (
              applications.map((application) => (
                <article className="tracker-item" key={application.job_id}>
                  <div>
                    <strong>{application.job_title}</strong>
                    <p>{application.company} · {application.location}</p>
                    {application.job_url && (
                      <a href={application.job_url} target="_blank" rel="noopener noreferrer">
                        Original posting ↗
                      </a>
                    )}
                  </div>

                  <select
                    value={application.status}
                    onChange={(event) =>
                      updateApplication(application.job_id, event.target.value)
                    }
                  >
                    <option value="Saved">Saved</option>
                    <option value="Applied">Applied</option>
                    <option value="Interview">Interview</option>
                    <option value="Rejected">Rejected</option>
                    <option value="Offer">Offer</option>
                  </select>

                  <button
                    className="remove-button"
                    onClick={() => deleteApplication(application.job_id)}
                  >
                    Remove
                  </button>
                </article>
              ))
            )}
          </section>
        )}

        <section className="search-panel">
          <div className="section-heading">
            <div>
              <h2>Explore opportunities</h2>
              <p>Search the collected job market dataset.</p>
            </div>
          </div>

          <div className="filters">
            <input
              type="text"
              placeholder="Search job title, company, or skills..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

            <input
              type="text"
              placeholder="Filter by location..."
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />

            <select
              value={remoteType}
              onChange={(e) => setRemoteType(e.target.value)}
            >
              <option value="">All work arrangements</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">On-site</option>
            </select>
          </div>
        </section>

        <section className="results">
          <div className="results-heading">
            <h2>Available jobs</h2>
            <span>{loading ? 'Loading...' : `${jobs.length} results`}</span>
          </div>

          {loading && <p className="message">Loading job listings...</p>}
          {error && <p className="error">{error}</p>}

          {!loading && !error && jobs.length === 0 && (
            <p className="message">No matching jobs found. Try different filters.</p>
          )}

          <div className="job-grid">
            {jobs.map((job) => (
              <article className="job-card" key={job.job_id}>
                <div className="job-top">
                  <span className="source">{job.source || 'Job listing'}</span>
                  <span className="work-type">
                    {job.remote_type || 'Work type unspecified'}
                  </span>
                </div>

                <h3>{job.job_title || 'Untitled position'}</h3>
                <p className="company">{job.company || 'Company not specified'}</p>

                <div className="job-details">
                  <span>📍 {job.location || 'Location not specified'}</span>
                  {job.job_type && <span>💼 {job.job_type}</span>}
                </div>

                {(job.salary_min != null || job.salary_max != null) && (
                  <p className="salary">
                    Salary: {job.salary_currency || ''}
                    {' '}
                    {job.salary_min ?? 'Not specified'}
                    {' – '}
                    {job.salary_max ?? 'Not specified'}
                    {job.salary_period && job.salary_period !== 'unknown'
                      ? ` / ${job.salary_period}`
                      : ' (period unverified)'}
                  </p>
                )}

                {job.skills && (
                  <p className="skills">
                    <strong>Skills:</strong> {job.skills}
                  </p>
                )}

                <div className="card-footer">
                  <span>{job.country || 'Country unspecified'}</span>
                  {job.job_url ? (
                    <a
                      href={job.job_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View original job ↗
                    </a>
                  ) : (
                    <span>Link unavailable</span>
                  )}
                </div>

                {/* Save / Tracker Button per card */}
                {savedIds.includes(job.job_id) ? (
                  <button
                    className="save-button saved"
                    onClick={() => setTrackerOpen(true)}
                  >
                    ✓ Saved — View Tracker
                  </button>
                ) : (
                  <button
                    className="save-button"
                    onClick={() => saveJob(job.job_id)}
                  >
                    + Save Job
                  </button>
                )}
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer>
        Job Market Analytics · Built with React, FastAPI, Python and SQLite
      </footer>
    </div>
  )
}

export default App