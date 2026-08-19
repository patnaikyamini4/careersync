import streamlit as st

# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="CareerSync",
    page_icon="💼",
    layout="centered",
)

# ---------------------------------------------------------
# Theme (custom CSS — navy / amber / mono editorial style)
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root {
    --bg: #0F1420;
    --surface: #161B2C;
    --border: #2A3149;
    --text: #EDEFF7;
    --text-muted: #8B92AC;
    --accent: #E8A33D;
    --matched: #4FB286;
    --missing: #E2685C;
}

.stApp { background-color: var(--bg); }

/* Prevent Streamlit's rerun dimming from making dark text unreadable */
[data-stale="true"] {
    opacity: 1 !important;
}

/* Recolor the top toolbar so it matches the theme instead of staying white */
header[data-testid="stHeader"] {
    background-color: var(--bg) !important;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: var(--text);
}

h1, h2, h3, h4, h5, h6 {
    color: #EDEFF7 !important;
}

p, label, [data-testid="stMarkdownContainer"] {
    color: #EDEFF7;
}

h1, h2, h3 {
    font-family: 'Fraunces', serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
}

.eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.16em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 6px;
}

/* ---------------------------------------------------------
   Resume uploader — ONLY the Upload button is clickable
   --------------------------------------------------------- */

[data-testid="stFileUploaderDropzone"] {
    background-color: #141A2A !important;
    border: 1px dashed #3A435F !important;
    border-radius: 12px !important;
    padding: 8px !important;
    transition: border-color 0.2s ease, background-color 0.2s ease;
    pointer-events: none !important;
}

[data-testid="stFileUploaderDropzone"] button {
    pointer-events: auto !important;
    cursor: pointer !important;
}

[data-testid="stFileUploaderDropzone"]:has(button:hover) {
    background-color: #181F32 !important;
    border-color: var(--accent) !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] {
    color: #AEB6CC !important;
    opacity: 1 !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] * {
    color: #AEB6CC !important;
    opacity: 1 !important;
}

[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span {
    color: #AEB6CC !important;
    opacity: 1 !important;
}

[data-testid="stFileUploaderDropzone"] svg {
    color: var(--accent) !important;
}

[data-testid="stFileUploaderDropzone"] button {
    background-color: #EDEFF7 !important;
    color: #1A2233 !important;
    border: none !important;
}

[data-testid="stFileUploaderDropzone"] button * {
    color: #1A2233 !important;
}

[data-testid="stFileUploaderDropzone"] button:hover {
    background-color: #FFFFFF !important;
    color: #1A2233 !important;
}

[data-testid="stFileUploaderDropzone"] button:hover * {
    color: #1A2233 !important;
}

/* ---------------------------------------------------------
   Job Description
   --------------------------------------------------------- */

.stTextArea textarea {
    background-color: #161B2C !important;
    color: #EDEFF7 !important;
    border: 1px solid #303851 !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    padding: 16px !important;
    box-shadow: none !important;
    transition:
        border-color 0.2s ease,
        box-shadow 0.2s ease,
        background-color 0.2s ease;
}

.stTextArea textarea::placeholder {
    color: #8B92AC !important;
    opacity: 1 !important;
}

.stTextArea textarea:focus {
    border-color: #E8A33D !important;
    background-color: #181F32 !important;
    box-shadow:
        0 0 0 1px rgba(232, 163, 61, 0.18),
        0 8px 24px rgba(0, 0, 0, 0.12) !important;
    outline: none !important;
}

.stTextArea label {
    color: #EDEFF7 !important;
    font-weight: 500 !important;
    font-size: 14px !important;
}

.stButton > button {
    background-color: var(--accent) !important;
    color: #1A1204 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.6rem !important;
    transition: background-color 0.15s ease;
}
.stButton > button:hover { background-color: #F0B457 !important; }

[data-testid="stDownloadButton"] > button {
    background-color: transparent !important;
    color: var(--accent) !important;
    border: 1.5px solid var(--accent) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.8rem !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background-color: rgba(232, 163, 61, 0.1) !important;
    color: #F0B457 !important;
    border-color: #F0B457 !important;
}

hr { border-color: var(--border) !important; margin: 20px 0 !important; }

/* ---------------------------------------------------------
   Results page — redesigned components
   --------------------------------------------------------- */

.section-head { margin: 4px 0 14px 0; }
.section-title {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 22px;
    color: var(--text);
    margin: 0;
}
.section-sub {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    color: var(--text-muted);
    margin-top: 3px;
}

/* Status card */
.status-card {
    display: flex;
    align-items: center;
    gap: 12px;
    background-color: var(--surface);
    border: 1px solid rgba(79,178,134,0.35);
    border-left: 3px solid var(--matched);
    border-radius: 10px;
    padding: 12px 18px;
    margin: 6px 0 6px 0;
}
.status-icon {
    color: var(--matched);
    font-size: 18px;
    font-weight: 700;
}
.status-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.1em;
    color: var(--matched);
    font-weight: 600;
}
.status-desc {
    font-size: 13.5px;
    color: var(--text-muted);
    margin-top: 1px;
}

/* Analyzed-resume filename line */
.status-file {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 4px;
}

.status-file span {
    color: var(--text);
    font-weight: 600;
}

/* Hero score card */
.hero-card {
    background: linear-gradient(180deg, #161B2C 0%, #131826 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px 30px;
    margin: 6px 0 24px 0;
    box-shadow: 0 12px 32px rgba(0,0,0,0.28);
}
.hero-flex {
    display: flex;
    align-items: center;
    gap: 36px;
    flex-wrap: wrap;
}
.hero-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.16em;
    color: var(--text-muted);
    text-transform: uppercase;
}
.hero-verdict {
    font-family: 'Fraunces', serif;
    font-weight: 700;
    font-size: 26px;
    color: var(--accent);
    margin: 6px 0 6px 0;
    letter-spacing: 0.01em;
    text-transform: uppercase;
}
.hero-sub {
    font-size: 14.5px;
    color: var(--text-muted);
    max-width: 360px;
    line-height: 1.5;
}
.hero-metrics {
    display: flex;
    gap: 28px;
    margin-top: 18px;
}
.metric-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 22px;
    font-weight: 600;
    color: var(--text);
}
.metric-num-matched { color: var(--matched); }
.metric-num-missing { color: var(--missing); }
.metric-label {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 2px;
}

/* Skills cards */
/* after */
.skills-row {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    margin: 6px 0 40px 0;
}
.skills-card {
    flex: 1;
    min-width: 260px;
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px 22px;
}
.skills-card-matched { border-top: 3px solid var(--matched); }
.skills-card-missing { border-top: 3px solid var(--missing); }
.skills-card-title {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 17px;
    color: var(--text);
}
.skills-card-count {
    display: block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 2px;
    margin-bottom: 14px;
}
.badge {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 20px;
    margin: 3px 6px 3px 0;
    font-size: 14px;
    font-family: 'Inter', sans-serif;
}
.badge-matched { background-color: rgba(79,178,134,0.14); color: var(--matched); border: 1px solid rgba(79,178,134,0.35); }
.badge-missing { background-color: rgba(226,104,92,0.14); color: var(--missing); border: 1px solid rgba(226,104,92,0.35); }

/* Insight (feedback) cards */
.insight-card {
    display: flex;
    gap: 16px;
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 10px;
    padding: 14px 18px;
    margin: 10px 0;
}
.insight-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    color: var(--accent);
    font-weight: 600;
    padding-top: 2px;
    min-width: 22px;
}
.insight-text {
    font-size: 15px;
    color: var(--text);
    line-height: 1.5;
}

/* Verdict (recruiter summary) card */
.verdict-card {
    background: linear-gradient(180deg, rgba(79,178,134,0.10) 0%, rgba(79,178,134,0.03) 100%);
    border: 1px solid rgba(79,178,134,0.35);
    border-left: 3px solid var(--matched);
    border-radius: 12px;
    padding: 18px 22px;
    margin: 6px 0 20px 0;
}
.verdict-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11.5px;
    letter-spacing: 0.12em;
    color: var(--matched);
    text-transform: uppercase;
    margin-bottom: 6px;
}
.verdict-text {
    font-family: 'Fraunces', serif;
    font-size: 17px;
    color: var(--text);
    line-height: 1.5;
}

@media (max-width: 700px) {
    .hero-flex { flex-direction: column; align-items: flex-start; }
    .hero-metrics { gap: 32px; }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Mock result based on shared/schema.json
# ---------------------------------------------------------
MOCK_RESULT = {
    "match_score": 78,
    "matched_skills": ["Python", "SQL", "REST APIs"],
    "missing_skills": ["Docker", "Kubernetes"],
    "candidate_feedback": [
        "Quantify your impact in the ML project bullet — add a metric.",
        "Move your Python/SQL skills higher, they match the JD's top requirement.",
    ],
    "recruiter_summary": "Strong technical fit, missing containerization experience.",
}

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.markdown('<div class="eyebrow">Resume Diagnostics</div>', unsafe_allow_html=True)
st.title("CareerSync")
st.write("Upload your resume and paste the job description to see how well they match.")

# ---------------------------------------------------------
# Resume upload
# ---------------------------------------------------------
resume = st.file_uploader(
    "Upload your Resume",
    type=["pdf", "docx"],
    help="Upload your resume as a PDF or DOCX file.",
)

# ---------------------------------------------------------
# Job description
# ---------------------------------------------------------
job_description = st.text_area(
    "Job Description",
    placeholder="Paste the job description here...",
    height=200,
)

# ---------------------------------------------------------
# Analyze button
# ---------------------------------------------------------
if st.button("Analyze Resume", type="primary"):

    if resume is None:
        st.warning("Please upload a resume.")

    elif not job_description.strip():
        st.warning("Please enter the job description.")

    else:
        with st.spinner("Analyzing..."):
            result = MOCK_RESULT

        score = result["match_score"]
        matched_skills = result["matched_skills"]
        missing_skills = result["missing_skills"]
        n_matched = len(matched_skills)
        n_missing = len(missing_skills)

        verdict = (
            "Strong alignment" if score >= 75
            else "Partial alignment" if score >= 50
            else "Limited alignment"
        )
        verdict_sub = {
            "Strong alignment": "Your resume shows strong alignment with this role.",
            "Partial alignment": "Your resume shows partial alignment with this role.",
            "Limited alignment": "Your resume shows limited alignment with this role.",
        }[verdict]

        # -------------------------------------------------
        # 1. Analysis complete — status card + analyzed filename
        # -------------------------------------------------
        st.markdown(f"""
        <div class="status-card">
            <div class="status-icon">✓</div>
            <div>
              <div class="status-title">ANALYSIS COMPLETE</div>
              <div class="status-desc">Resume successfully evaluated against the job description.</div>
              <div class="status-file">Analyzed resume: <span>{resume.name}</span></div>
            </div>
          </div>
        
        """, unsafe_allow_html=True)

        # -------------------------------------------------
        # 2. Match score — hero section
        # -------------------------------------------------
        circumference = 2 * 3.14159 * 60
        dash = circumference * score / 100

        st.markdown(f"""
        <div class="hero-card">
          <div class="hero-flex">
            <svg width="160" height="160" viewBox="0 0 160 160">
              <circle cx="80" cy="80" r="60" fill="none" stroke="#2A3149" stroke-width="14"/>
              <circle cx="80" cy="80" r="60" fill="none" stroke="#E8A33D" stroke-width="14"
                stroke-dasharray="{dash:.1f} {circumference:.1f}"
                stroke-linecap="round"
                transform="rotate(-90 80 80)"/>
              <text x="80" y="90" text-anchor="middle" font-family="IBM Plex Mono, monospace"
                font-size="32" font-weight="600" fill="#EDEFF7">{score}%</text>
            </svg>
            <div>
              <div class="hero-label">Match Score</div>
              <div class="hero-verdict">{verdict}</div>
              <div class="hero-sub">{verdict_sub}</div>
              <div class="hero-metrics">
                <div>
                  <div class="metric-num metric-num-matched">{n_matched}</div>
                  <div class="metric-label">Matched skills</div>
                </div>
                <div>
                  <div class="metric-num metric-num-missing">{n_missing}</div>
                  <div class="metric-label">Skills to strengthen</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # -------------------------------------------------
        # 3. Matched / missing skills cards
        # -------------------------------------------------
        matched_badges = "".join(
            f'<span class="badge badge-matched">✓ {s}</span>' for s in matched_skills
        )
        missing_badges = "".join(
            f'<span class="badge badge-missing">✕ {s}</span>' for s in missing_skills
        )

        st.markdown(f"""
        <div class="skills-row">
          <div class="skills-card skills-card-matched">
            <div class="skills-card-title">Matched Skills</div>
            <span class="skills-card-count">{n_matched} skill{'s' if n_matched != 1 else ''} found</span>
            {matched_badges}
          </div>
          <div class="skills-card skills-card-missing">
            <div class="skills-card-title">Skills to Strengthen</div>
            <span class="skills-card-count">{n_missing} skill{'s' if n_missing != 1 else ''} missing</span>
            {missing_badges}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # -------------------------------------------------
        # 4. Candidate insights
        # -------------------------------------------------
        st.markdown("""
        <div class="section-head">
          <div class="section-title">Candidate Insights</div>
          <div class="section-sub">Actionable changes that could improve your match.</div>
        </div>
        """, unsafe_allow_html=True)

        for i, feedback in enumerate(result["candidate_feedback"], start=1):
            st.markdown(f"""
            <div class="insight-card">
              <div class="insight-num">{i:02d}</div>
              <div class="insight-text">{feedback}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # -------------------------------------------------
        # 5. Recruiter verdict
        # -------------------------------------------------
        st.markdown("""
        <div class="section-head">
          <div class="section-title">Recruiter Verdict</div>
          <div class="section-sub">How a recruiter may view your profile.</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="verdict-card">
          <div class="verdict-label">Recruiter Verdict</div>
          <div class="verdict-text">{result['recruiter_summary']}</div>
        </div>
        """, unsafe_allow_html=True)

        # -------------------------------------------------
        # 6. Download report
        # -------------------------------------------------
        report_text = f"""CareerSync — Resume Analysis Report

Overall Match: {result['match_score']}%

Matched Skills: {', '.join(result['matched_skills'])}
Missing Skills: {', '.join(result['missing_skills'])}

Candidate Feedback:
{chr(10).join(f"- {tip}" for tip in result['candidate_feedback'])}

Recruiter Summary:
{result['recruiter_summary']}
"""

        st.download_button(
            label="↓  Download Report",
            data=report_text,
            file_name="careersync_report.txt",
            mime="text/plain",
        )