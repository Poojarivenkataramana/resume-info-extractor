"""
app.py
------
Streamlit UI for the Resume/JD Information Extraction Tool.

Run with:
    streamlit run app.py
"""

from pathlib import Path
import streamlit as st
import pandas as pd

from extractor import extract, compare_to_jd

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_RESUME_PATH = BASE_DIR / "sample_data" / "sample_resume.txt"
SAMPLE_JD_PATH = BASE_DIR / "sample_data" / "sample_job_description.txt"

st.set_page_config(page_title="Resume Info Extractor", page_icon="🧠", layout="wide")

st.title("🧠 Resume & Job Description Information Extractor")
st.caption(
    "NLP pipeline (spaCy NER + regex + skills taxonomy matching) that extracts "
    "structured data from unstructured resume/JD text, and scores skill match "
    "between the two."
)

with st.sidebar:
    st.header("About this project")
    st.write(
        "This tool combines three extraction techniques:\n\n"
        "1. **Regex** — email, phone, LinkedIn/GitHub URLs, years of experience\n"
        "2. **spaCy NER** — candidate name, organizations, locations\n"
        "3. **Taxonomy matching** — 100+ curated skill terms across 7 categories\n\n"
        "Built by Venkataramana Poojari."
    )
    st.markdown("---")
    use_sample = st.checkbox("Load sample resume + JD", value=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Resume")
    default_resume = ""
    if use_sample and SAMPLE_RESUME_PATH.exists():
        with open(SAMPLE_RESUME_PATH, "r", encoding="utf-8") as f:
            default_resume = f.read()
    resume_text = st.text_area("Paste resume text", value=default_resume, height=350)

with col2:
    st.subheader("📋 Job Description (optional)")
    default_jd = ""
    if use_sample and SAMPLE_JD_PATH.exists():
        with open(SAMPLE_JD_PATH, "r", encoding="utf-8") as f:
            default_jd = f.read()
    jd_text = st.text_area("Paste job description text", value=default_jd, height=350)

if st.button("Extract Information", type="primary"):
    if not resume_text.strip():
        st.warning("Please paste resume text first.")
    else:
        result = extract(resume_text)

        st.markdown("## 📊 Extracted Resume Data")

        c1, c2, c3 = st.columns(3)
        c1.metric("Name", result.name or "Not found")
        c2.metric("Years Experience", result.years_experience or "Not found")
        c3.metric("Total Skills Found", len(result.all_skills))

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Contact Info**")
            st.write(f"📧 Email: {', '.join(result.emails) or '—'}")
            st.write(f"📱 Phone: {', '.join(result.phones) or '—'}")
            st.write(f"🔗 LinkedIn: {result.linkedin or '—'}")
            st.write(f"💻 GitHub: {result.github or '—'}")
        with c2:
            st.markdown("**Education**")
            if result.education:
                for edu in result.education:
                    st.write(f"🎓 {edu}")
            else:
                st.write("—")

        st.markdown("**Skills by Category**")
        if result.skills_by_category:
            for category, skills in result.skills_by_category.items():
                st.write(f"**{category}:** {', '.join(skills)}")
        else:
            st.write("No skills matched.")

        if result.organizations:
            st.markdown("**Organizations Detected**")
            st.write(", ".join(result.organizations))

        with st.expander("View raw JSON output"):
            st.json(result.to_dict())

        # --- JD comparison ---
        if jd_text.strip():
            st.markdown("---")
            st.markdown("## 🎯 Resume vs Job Description Match")

            comparison = compare_to_jd(resume_text, jd_text)
            match_pct = comparison["match_percentage"]

            st.progress(min(max(float(match_pct) / 100.0, 0.0), 1.0))
            st.markdown(f"### Match Score: **{match_pct}%**")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("✅ **Matched Skills**")
                st.write(", ".join(comparison["matched_skills"]) or "—")
            with c2:
                st.markdown("❌ **Missing Skills**")
                st.write(", ".join(comparison["missing_skills"]) or "—")
            with c3:
                st.markdown("➕ **Extra Skills (not in JD)**")
                st.write(", ".join(comparison["extra_skills"]) or "—")

st.markdown("---")
st.caption("Project source: github.com/Poojarivenkataramana/resume-info-extractor")
