# Resume & Job Description Information Extraction Tool

An NLP pipeline that extracts structured data (contact info, skills, education,
experience) from unstructured resume and job description text, and scores how
well a resume matches a given job description.

**Live demo:** run locally with Streamlit (see below) — screen recording in
`/demo` or linked in the LinkedIn post.

## Why this project

Resumes and job postings are unstructured text with no fixed schema, which
makes them a good real-world test case for information extraction: the kind
of problem where you can't just grab one library and call it done. Different
fields need different extraction strategies, and figuring out *which*
strategy fits *which* field is the actual engineering decision here.

## Approach

This project deliberately combines three extraction techniques instead of
relying on one:

| Field type | Technique | Why |
|---|---|---|
| Email, phone, LinkedIn/GitHub URLs, years of experience | **Regex** | Format is highly predictable — high precision, no ML needed |
| Candidate name, organizations, locations | **spaCy NER** (`en_core_web_sm`) | Position and phrasing vary too much for regex; needs contextual understanding |
| Technical skills (100+ terms, 7 categories) | **Curated taxonomy + phrase matching** | General-purpose NER doesn't reliably tag domain terms like "pandas" or "FastAPI" as entities |
| Education | **Section-aware parsing** | Anchored on common resume section headers, then filtered by degree keywords |

A known limitation, and worth stating rather than hiding: spaCy's small NER
model, run on skills-dense resume text, occasionally mis-tags tech terms as
organizations. This project filters those out by cross-checking NER output
against the skills taxonomy — a concrete example of combining rule-based and
statistical NLP rather than trusting either one blindly.

## Features

- Extracts: name, email, phone, LinkedIn, GitHub, years of experience,
  organizations, locations, education, and categorized skills
- Compares a resume against a job description and produces a **match
  percentage**, plus matched / missing / extra skill lists
- CLI for quick testing, Streamlit UI for a live interactive demo
- Skills taxonomy is easily extensible — just add terms to `skills_db.py`

## Project structure

```
resume-extractor/
├── extractor.py          # Core extraction engine (regex + NER + taxonomy)
├── skills_db.py           # Curated skills taxonomy (100+ terms, 7 categories)
├── cli.py                  # Command-line interface
├── app.py                  # Streamlit web UI
├── requirements.txt
├── sample_data/
│   ├── sample_resume.txt
│   └── sample_job_description.txt
└── README.md
```

## Setup

```bash
git clone https://github.com/Poojarivenkataramana/resume-info-extractor.git
cd resume-info-extractor
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Usage

**CLI:**
```bash
python cli.py sample_data/sample_resume.txt
python cli.py sample_data/sample_resume.txt --jd sample_data/sample_job_description.txt
```

**Web UI:**
```bash
streamlit run app.py
```
Then paste in any resume and job description text to see extraction and
match scoring live.

## Example output

```json
{
  "name": "Venkataramana Poojari",
  "emails": ["poojarivenkataramana@gmail.com"],
  "years_experience": "1 year experience",
  "education": ["Bachelor of Technology, Electronics and Communication Engineering"],
  "skills_by_category": {
    "Programming Languages": ["python", "sql"],
    "Data Science & ML": ["machine learning", "nlp", "information extraction"],
    "Data Analysis & Visualization": ["pandas", "numpy", "tableau"]
  }
}
```

Match scoring against a sample Data Analyst job description: **70% match**,
with missing skills (`aws`, `docker`, `power bi`) surfaced explicitly —
directly actionable for a candidate deciding what to learn next.

## Possible extensions

- Swap `en_core_web_sm` for a fine-tuned NER model trained on labeled resume
  data for higher precision on names/orgs
- PDF/DOCX upload support (currently plain text)
- Batch mode: score multiple resumes against one JD and rank them

## Tech stack

Python · spaCy · regex · Streamlit · pandas
