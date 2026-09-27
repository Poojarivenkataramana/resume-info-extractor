"""
skills_db.py
------------
A curated skills taxonomy used for keyword-based skill matching.
Organized by category so the extractor can also report skill *breadth*
across categories (useful for resume screening / candidate comparison).

To extend: just add more terms to the relevant list. Matching is
case-insensitive and handles common separators (dots, plus signs, etc.)
via the normalization step in extractor.py.
"""

SKILLS_DB = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c",
        "sql", "r", "scala", "go", "golang", "rust", "php", "ruby",
        "matlab", "bash", "shell scripting", "html", "css",
    ],
    "Data Science & ML": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "reinforcement learning", "neural networks",
        "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras",
        "xgboost", "lightgbm", "random forest", "regression",
        "classification", "clustering", "time series analysis",
        "feature engineering", "model deployment", "mlops",
        "information extraction", "named entity recognition", "ner",
        "sentiment analysis", "text mining", "opencv", "hugging face",
        "transformers", "llm", "large language models", "prompt engineering",
        "generative ai", "genai",
    ],
    "Data Analysis & Visualization": [
        "pandas", "numpy", "eda", "exploratory data analysis",
        "data cleaning", "data wrangling", "matplotlib", "seaborn",
        "plotly", "tableau", "power bi", "excel", "data visualization",
        "statistics", "hypothesis testing", "a/b testing",
    ],
    "Databases": [
        "mysql", "postgresql", "postgres", "mongodb", "sqlite",
        "oracle", "nosql", "redis", "elasticsearch", "data warehousing",
        "etl", "snowflake", "bigquery",
    ],
    "Web & APIs": [
        "rest api", "restful api", "http", "fastapi", "flask", "django",
        "graphql", "web scraping", "beautifulsoup", "selenium",
        "requests", "api development",
    ],
    "Tools & Platforms": [
        "git", "github", "docker", "kubernetes", "aws", "azure",
        "gcp", "google cloud", "linux", "jira", "ci/cd", "airflow",
        "spark", "pyspark", "hadoop",
    ],
    "Soft Skills": [
        "communication", "teamwork", "leadership", "problem solving",
        "critical thinking", "time management", "collaboration",
        "adaptability", "project management",
    ],
}

# Flat lookup for fast matching: skill_text -> category
SKILL_TO_CATEGORY = {
    skill: category
    for category, skills in SKILLS_DB.items()
    for skill in skills
}
