import { useRef, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  const fileInputRef = useRef(null)

  const [resume, setResume] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleResumeChange = (event) => {
    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    const isPdf =
      file.type === 'application/pdf' ||
      file.name.toLowerCase().endsWith('.pdf')

    if (!isPdf) {
      setResume(null)
      setError('Please upload a PDF resume.')
      return
    }

    setResume(file)
    setError('')
    setResult(null)
  }

  const handleAnalyze = async (event) => {
    event.preventDefault()

    setError('')
    setResult(null)

    if (!resume) {
      setError('Please upload your resume PDF.')
      return
    }

    if (!jobDescription.trim()) {
      setError('Please enter the job description.')
      return
    }

    if (jobDescription.trim().length < 20) {
      setError('Please enter a more complete job description.')
      return
    }

    setLoading(true)

    try {
      const formData = new FormData()

      formData.append('resume', resume)
      formData.append('job_description', jobDescription.trim())

      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        body: formData,
      })

      let data

      try {
        data = await response.json()
      } catch {
        throw new Error('The backend returned an invalid response.')
      }

      if (!response.ok) {
        const message =
          typeof data?.detail === 'string'
            ? data.detail
            : 'Resume analysis failed.'

        throw new Error(message)
      }

      setResult(data)

      setTimeout(() => {
        document
          .getElementById('results')
          ?.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
          })
      }, 100)
    } catch (err) {
      if (err instanceof TypeError) {
        setError(
          'Cannot connect to CareerSync backend. Make sure FastAPI is running on http://127.0.0.1:8000.',
        )
      } else {
        setError(err.message || 'Something went wrong.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setResume(null)
    setJobDescription('')
    setResult(null)
    setError('')

    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleAnalyzeAnother = () => {
    setResume(null)
    setJobDescription('')
    setResult(null)
    setError('')

    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }

    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  }

  const getScoreClass = (score) => {
    if (score >= 75) {
      return 'score-high'
    }

    if (score >= 50) {
      return 'score-medium'
    }

    return 'score-low'
  }

  const getScoreLabel = (score) => {
    if (score >= 90) {
      return 'Excellent Match'
    }

    if (score >= 75) {
      return 'Strong Match'
    }

    if (score >= 50) {
      return 'Moderate Match'
    }

    return 'Needs Improvement'
  }

  const score = Number(result?.match_score ?? 0)

  return (
    <div className="app">

      {/* =====================================================
          NAVBAR
      ====================================================== */}

      <header className="navbar">
        <div className="brand">
          <div className="brand-logo">
            C
          </div>

          <div className="brand-text">
            <h1>CareerSync</h1>
            <p>AI Resume Analyzer</p>
          </div>
        </div>

        <div className="ai-status">
          <span className="status-dot"></span>
          Gemini AI
        </div>
      </header>

      {/* =====================================================
          MAIN
      ====================================================== */}

      <main className="main-container">

        {/* =================================================
            HERO
        ================================================== */}

        <section className="hero">

          <div className="hero-badge">
            AI-POWERED CAREER MATCHING
          </div>

          <h2>
            Match your resume with the
            <span> right opportunity.</span>
          </h2>

          <p>
            Upload your resume and compare it against any job
            description to discover your match score, relevant
            skills, missing skills, and personalized career
            recommendations.
          </p>

        </section>

        {/* =================================================
            ANALYSIS FORM
        ================================================== */}

        <form
          className="analysis-card"
          onSubmit={handleAnalyze}
        >

          <div className="form-grid">

            {/* =============================================
                RESUME
            ============================================== */}

            <div className="form-group">

              <label htmlFor="resume">
                Resume PDF
              </label>

              <div
                className={`upload-box ${
                  resume ? 'upload-box-selected' : ''
                }`}
              >

                <input
                  ref={fileInputRef}
                  id="resume"
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleResumeChange}
                />

                <div className="upload-icon">
                  <span>↑</span>
                </div>

                {resume ? (
                  <>
                    <div className="file-check">
                      ✓
                    </div>

                    <h3>
                      {resume.name}
                    </h3>

                    <p>
                      {(resume.size / 1024 / 1024).toFixed(2)} MB
                    </p>

                    <span className="change-file">
                      Click to change file
                    </span>
                  </>
                ) : (
                  <>
                    <h3>
                      Upload your resume
                    </h3>

                    <p>
                      Click here or drag a PDF file
                    </p>

                    <span>
                      PDF only • Max supported size
                    </span>
                  </>
                )}

              </div>

            </div>

            {/* =============================================
                JOB DESCRIPTION
            ============================================== */}

            <div className="form-group">

              <label htmlFor="job-description">
                Job Description
              </label>

              <textarea
                id="job-description"
                value={jobDescription}
                onChange={(event) => {
                  setJobDescription(event.target.value)
                  setError('')
                  setResult(null)
                }}
                placeholder="Paste the complete job description here..."
              />

              <div className="character-count">
                {jobDescription.length} characters
              </div>

            </div>

          </div>

          {/* =================================================
              ERROR
          ================================================== */}

          {error && (
            <div className="error-box">
              <div className="error-icon">
                !
              </div>

              <div>
                <strong>
                  Unable to continue
                </strong>

                <span>
                  {error}
                </span>
              </div>
            </div>
          )}

          {/* =================================================
              BUTTONS
          ================================================== */}

          <div className="form-buttons">

            <button
              type="button"
              className="clear-button"
              onClick={handleClear}
              disabled={loading}
            >
              Clear
            </button>

            <button
              type="submit"
              className="analyze-button"
              disabled={loading}
            >

              {loading ? (
                <>
                  <span className="spinner"></span>
                  Analyzing Resume...
                </>
              ) : (
                <>
                  Analyze Resume
                  <span className="arrow">→</span>
                </>
              )}

            </button>

          </div>

        </form>

        {/* =================================================
            LOADING
        ================================================== */}

        {loading && (
          <section className="loading-card">

            <div className="loading-orbit">
              <div className="loading-dot"></div>
            </div>

            <div>
              <h3>
                Analyzing your resume
              </h3>

              <p>
                CareerSync is extracting your resume,
                comparing skills, and generating AI recommendations.
              </p>
            </div>

          </section>
        )}

        {/* =================================================
            RESULTS
        ================================================== */}

        {result && !loading && (
          <section
            id="results"
            className="results"
          >

            {/* =============================================
                RESULTS HEADER
            ============================================== */}

            <div className="results-header">

              <div className="results-heading">

                <div className="result-badge">
                  ANALYSIS COMPLETE
                </div>

                <h2>
                  Resume Analysis
                </h2>

                <p>
                  Here is your AI-powered resume and
                  job match analysis.
                </p>

              </div>

              {/* ===========================================
                  SCORE
              ============================================ */}

              <div className="score-card">

                <div
                  className={`score-ring ${getScoreClass(score)}`}
                  style={{
                    '--score': `${score * 3.6}deg`,
                  }}
                >
                  <div className="score-ring-inner">
                    <strong>
                      {score}
                    </strong>

                    <span>
                      %
                    </span>
                  </div>
                </div>

                <div className="score-label">
                  {getScoreLabel(score)}
                </div>

                <small>
                  Match Score
                </small>

              </div>

            </div>

            {/* =============================================
                SKILLS
            ============================================== */}

            <div className="skills-grid">

              {/* MATCHED */}

              <div className="result-card">

                <div className="result-card-title">

                  <div className="result-icon matched">
                    ✓
                  </div>

                  <div>
                    <h3>
                      Matched Skills
                    </h3>

                    <p>
                      {result.matched_skills?.length || 0}{' '}
                      skills found
                    </p>
                  </div>

                </div>

                <div className="skills">

                  {result.matched_skills?.length > 0 ? (
                    result.matched_skills.map((skill) => (
                      <span
                        className="skill matched-skill"
                        key={skill}
                      >
                        ✓ {skill}
                      </span>
                    ))
                  ) : (
                    <p className="empty">
                      No matching skills identified.
                    </p>
                  )}

                </div>

              </div>

              {/* MISSING */}

              <div className="result-card">

                <div className="result-card-title">

                  <div className="result-icon missing">
                    !
                  </div>

                  <div>
                    <h3>
                      Missing Skills
                    </h3>

                    <p>
                      {result.missing_skills?.length || 0}{' '}
                      skills to improve
                    </p>
                  </div>

                </div>

                <div className="skills">

                  {result.missing_skills?.length > 0 ? (
                    result.missing_skills.map((skill) => (
                      <span
                        className="skill missing-skill"
                        key={skill}
                      >
                        + {skill}
                      </span>
                    ))
                  ) : (
                    <p className="empty">
                      No major missing skills identified.
                    </p>
                  )}

                </div>

              </div>

            </div>

            {/* =============================================
                CANDIDATE FEEDBACK
            ============================================== */}

            <div className="result-card large-card">

              <div className="result-card-title">

                <div className="result-icon feedback">
                  ✦
                </div>

                <div>
                  <h3>
                    Candidate Feedback
                  </h3>

                  <p>
                    Personalized AI recommendations
                  </p>
                </div>

              </div>

              <div className="feedback-list">

                {result.candidate_feedback?.length > 0 ? (
                  result.candidate_feedback.map(
                    (feedback, index) => (
                      <div
                        className="feedback-item"
                        key={`${feedback}-${index}`}
                      >

                        <div className="feedback-number">
                          {String(index + 1).padStart(2, '0')}
                        </div>

                        <p>
                          {feedback}
                        </p>

                      </div>
                    ),
                  )
                ) : (
                  <p className="empty">
                    No additional feedback available.
                  </p>
                )}

              </div>

            </div>

            {/* =============================================
                RECRUITER SUMMARY
            ============================================== */}

            <div className="result-card large-card recruiter-card">

              <div className="result-card-title">

                <div className="result-icon recruiter">
                  ◆
                </div>

                <div>
                  <h3>
                    Recruiter Summary
                  </h3>

                  <p>
                    AI-generated candidate assessment
                  </p>
                </div>

              </div>

              <div className="recruiter-summary">
                {result.recruiter_summary}
              </div>

            </div>

            {/* =============================================
                ANALYZE ANOTHER
            ============================================== */}

            <div className="another-analysis">

              <div>
                <h3>
                  Want to analyze another resume?
                </h3>

                <p>
                  Upload a different resume and compare it
                  with another opportunity.
                </p>
              </div>

              <button
                type="button"
                onClick={handleAnalyzeAnother}
              >
                Analyze Another Resume
                <span>→</span>
              </button>

            </div>

          </section>
        )}

      </main>

      {/* =====================================================
          FOOTER
      ====================================================== */}

      <footer className="footer">

        <strong>
          CareerSync
        </strong>

        <span>
          AI-powered resume and job matching
        </span>

        <span className="footer-dot">
          •
        </span>

        <span>
          Powered by Gemini AI
        </span>

      </footer>

    </div>
  )
}

export default App