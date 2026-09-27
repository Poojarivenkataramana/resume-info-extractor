"""
extractor.py
------------
Core information-extraction engine for resumes and job descriptions.

Approach (hybrid, and deliberately so — this is the part worth explaining
in an interview):
  1. Regex rules for high-precision structured fields where format is
     predictable: email, phone, LinkedIn/GitHub URLs, years of experience.
  2. spaCy's pretrained NER model for fields that vary in phrasing and
     position: person name, organizations, locations, dates.
  3. Keyword/phrase matching against a curated skills taxonomy
     (skills_db.py) for skill extraction, since general-purpose NER
     doesn't reliably tag domain-specific tech terms like "pandas" or
     "FastAPI" as entities.
  4. Section-aware parsing for education, using common resume section
     headers as anchors.

Regex handles the "format is the signal" fields. NER handles the
"context is the signal" fields. Keyword matching handles the
"vocabulary is the signal" fields. Using one technique for everything
is the mistake this project deliberately avoids.
"""

import re
import spacy
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

from skills_db import SKILL_TO_CATEGORY

# Load once at module import — reused across all extractions.
# Auto-download model if not present to avoid startup crashes.
try:
    _NLP = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    _NLP = spacy.load("en_core_web_sm")

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,5}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{4,6}"
)

LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_/]+", re.I)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-_/]+", re.I)

# "3 years", "3+ years", "3-5 years of experience", "1 year experience"
EXPERIENCE_RE = re.compile(
    r"(\d{1,2}(?:\.\d+)?)\+?\s*(?:-\s*\d{1,2}\s*|to\s*\d{1,2}\s*)?years?\s+(?:of\s+)?(?:work\s+|professional\s+|relevant\s+|hands-on\s+|industry\s+)?experience",
    re.I,
)

SECTION_HEADERS = {
    "education": ["education", "academic background", "academic qualifications", "qualifications"],
    "experience": ["experience", "work experience", "professional experience", "employment history"],
    "projects": ["projects", "personal projects", "academic projects"],
    "skills": ["skills", "technical skills", "core competencies"],
    "certifications": ["certifications", "licenses", "licenses & certifications"],
}

DEGREE_PATTERNS = [
    r"\bb\.?tech\b", r"\bbtech\b", r"\bbachelor\b",
    r"\bm\.?tech\b", r"\bmtech\b", r"\bmaster\b",
    r"\bb\.e\b", r"\bb\.e\.\b", r"\bBE\b",
    r"\bm\.e\b", r"\bm\.e\.\b", r"\bME\b",
    r"\bb\.?sc\b", r"\bbsc\b",
    r"\bm\.?sc\b", r"\bmsc\b",
    r"\bmba\b", r"\bmca\b", r"\bbca\b", r"\bph\.?d\b", r"\bphd\b",
    r"\bdiploma\b", r"\bdegree\b",
]


@dataclass
class ExtractionResult:
    name: Optional[str] = None
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    linkedin: Optional[str] = None
    github: Optional[str] = None
    years_experience: Optional[str] = None
    organizations: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    education: List[str] = field(default_factory=list)
    skills_by_category: Dict[str, List[str]] = field(default_factory=dict)
    all_skills: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# Field-level extraction functions
# ---------------------------------------------------------------------------

def extract_contact_info(text: str) -> Dict:
    raw_emails = EMAIL_RE.findall(text)
    emails = list(dict.fromkeys(e.rstrip(".") for e in raw_emails if e))
    phones_raw = PHONE_RE.findall(text)
    # Filter out short false positives and ensure 10-15 digits
    phones = list(dict.fromkeys(
        p.strip() for p in phones_raw
        if 10 <= len(re.sub(r"\D", "", p)) <= 15
    ))
    linkedin_match = LINKEDIN_RE.search(text)
    github_match = GITHUB_RE.search(text)
    return {
        "emails": emails,
        "phones": phones,
        "linkedin": linkedin_match.group(0) if linkedin_match else None,
        "github": github_match.group(0) if github_match else None,
    }


def extract_years_experience(text: str) -> Optional[str]:
    match = EXPERIENCE_RE.search(text)
    return match.group(0).strip() if match else None


def extract_named_entities(text: str) -> Dict:
    """Use spaCy NER for name, organizations, and locations."""
    # Limit to first 500 chars for name detection — name is almost
    # always near the top, and this avoids picking up a random
    # PERSON-tagged reference name from the middle of the document.
    doc_head = _NLP(text[:500])
    doc_full = _NLP(text)

    name = None
    for ent in doc_head.ents:
        if ent.label_ == "PERSON":
            cleaned_name = ent.text.strip().split("\n")[0].strip()
            if cleaned_name:
                name = cleaned_name
                break

    # If NER didn't find person in doc_head, check first non-empty line as fallback
    if not name:
        for line in text.split("\n"):
            line_clean = line.strip()
            if line_clean and not EMAIL_RE.search(line_clean) and not PHONE_RE.search(line_clean):
                if len(line_clean.split()) <= 4 and not any(c in line_clean for c in ":|/\\@"):
                    name = line_clean
                break

    # spaCy's small model, run on skills-dense resume text, sometimes
    # tags tech terms (e.g. "Python", "Tableau") as ORG/GPE. Filter
    # anything that's actually in our skills taxonomy before returning.
    from skills_db import SKILL_TO_CATEGORY as _SKILLS
    def _is_skill_term(val: str) -> bool:
        t_clean = val.strip().lower()
        if t_clean in _SKILLS:
            return True
        parts = [p.strip() for p in re.split(r"[,/|;]", t_clean) if p.strip()]
        return bool(parts) and all(p in _SKILLS for p in parts)

    orgs = []
    for ent in doc_full.ents:
        if ent.label_ == "ORG":
            cleaned = " ".join(ent.text.split())
            if cleaned and not _is_skill_term(cleaned) and cleaned not in orgs:
                orgs.append(cleaned)

    locations = []
    for ent in doc_full.ents:
        if ent.label_ in ("GPE", "LOC"):
            cleaned = " ".join(ent.text.split())
            if cleaned and not _is_skill_term(cleaned) and cleaned not in locations:
                locations.append(cleaned)

    return {"name": name, "organizations": orgs[:15], "locations": locations[:10]}


def extract_skills(text: str) -> Dict:
    """Keyword-match against the curated skills taxonomy.

    Matching is done on a normalized, lowercased copy of the text with
    word boundaries respected, so 'r' (the language) doesn't match
    inside 'analyzer', etc. Multi-word skills are matched as phrases.
    """
    text_lower = " " + re.sub(r"[/,;()]", " ", text.lower()) + " "

    found = {}
    for skill, category in SKILL_TO_CATEGORY.items():
        # Prevent partial overlaps with symbols like + and # (e.g. 'c' matching in 'c++' or 'c#')
        trailing_check = r"(?![a-z0-9+#])" if not any(c in skill for c in "+#") else r"(?![a-z0-9])"
        leading_check = r"(?<![a-z0-9+#])" if not any(c in skill for c in "+#") else r"(?<![a-z0-9])"
        pattern = leading_check + re.escape(skill) + trailing_check
        if re.search(pattern, text_lower):
            found.setdefault(category, []).append(skill)

    all_skills = sorted({s for skills in found.values() for s in skills})
    return {"skills_by_category": found, "all_skills": all_skills}


def _get_section(text: str, header_variants: List[str]) -> Optional[str]:
    """Grab the text block following a section header, up to the next
    section header or end of document. Simple but effective for
    reasonably well-formatted resumes."""
    lines = text.split("\n")
    all_headers_lower = [
        h.lower() for headers in SECTION_HEADERS.values() for h in headers
    ]
    variants = [h.lower() for h in header_variants]

    def _clean_header(line: str) -> str:
        return line.strip().lower().strip("#*-_ :\t")

    start_idx = None
    for i, line in enumerate(lines):
        line_clean = _clean_header(line)
        if line_clean in variants:
            start_idx = i + 1
            break
    if start_idx is None:
        return None

    end_idx = len(lines)
    for i in range(start_idx, len(lines)):
        line_clean = _clean_header(lines[i])
        if line_clean in all_headers_lower and line_clean:
            end_idx = i
            break

    return "\n".join(lines[start_idx:end_idx]).strip()


def extract_education(text: str) -> List[str]:
    section = _get_section(text, SECTION_HEADERS["education"])
    search_text = section if section else text

    results = []
    for line in search_text.split("\n"):
        line_clean = line.strip()
        if not line_clean:
            continue
        for pat in DEGREE_PATTERNS:
            flags = 0 if any(c.isupper() for c in pat if c.isalpha()) else re.I
            if re.search(pat, line_clean, flags):
                results.append(line_clean)
                break
    return results[:6]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def extract(text: str) -> ExtractionResult:
    """Run the full extraction pipeline on raw resume/JD text."""
    contact = extract_contact_info(text)
    entities = extract_named_entities(text)
    skills = extract_skills(text)
    education = extract_education(text)
    years_exp = extract_years_experience(text)

    return ExtractionResult(
        name=entities["name"],
        emails=contact["emails"],
        phones=contact["phones"],
        linkedin=contact["linkedin"],
        github=contact["github"],
        years_experience=years_exp,
        organizations=entities["organizations"],
        locations=entities["locations"],
        education=education,
        skills_by_category=skills["skills_by_category"],
        all_skills=skills["all_skills"],
    )


def compare_to_jd(resume_text: str, jd_text: str) -> Dict:
    """Compare a resume's extracted skills against a job description's
    required skills — the practical use case: quick match scoring."""
    resume_skills = set(extract_skills(resume_text)["all_skills"])
    jd_skills = set(extract_skills(jd_text)["all_skills"])

    matched = sorted(resume_skills & jd_skills)
    missing = sorted(jd_skills - resume_skills)
    extra = sorted(resume_skills - jd_skills)

    match_pct = round(100 * len(matched) / len(jd_skills), 1) if jd_skills else 0.0

    return {
        "match_percentage": match_pct,
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra,
    }
