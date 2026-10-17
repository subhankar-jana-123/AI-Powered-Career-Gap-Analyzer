# AI-Powered Career Gap Analyzer (v2)

Compares a student's skills with job-description requirements for 44 tech roles, plus a custom target role option, then
recommends missing skills, learning priorities and best-fit roles. Animated Streamlit UI.

## Run
```bash
pip install -r requirements.txt
python -m src.generate_data     # (optional) regenerate sample postings for all roles
python -m src.pipeline          # skill extraction + clustering -> SQLite + Power BI CSVs
streamlit run app.py
```

## Files
- `src/skills.py`     skill taxonomy (category, weeks to learn, aliases)
- `src/roles.py`      tech roles and their core/optional skills (add roles here)
- `src/generate_data.py` creates `data/sample_jobs.csv` (or use real data: title,company,description)
- `src/skill_extractor.py` NLP skill extraction · `src/clustering.py` TF-IDF + KMeans
- `src/matcher.py`    gap analysis, priorities, role recommendations
- `src/database.py`   SQLite + SQL · `src/pipeline.py` ETL + exports to `powerbi/`

## Add a role
Add skills to `src/skills.py` if needed, add an entry to `ROLES` in `src/roles.py`, then run
`python -m src.generate_data` and `python -m src.pipeline`.

## Power BI
Get Data -> Text/CSV -> load `powerbi/*.csv`. Relationships: `jobs[job_id]` 1-* `job_skills[job_id]`,
`skills[skill]` 1-* `job_skills[skill]`. Measures:
```
Total Jobs = DISTINCTCOUNT(jobs[job_id])
Demand % = DIVIDE(DISTINCTCOUNT(job_skills[job_id]), [Total Jobs])
```
