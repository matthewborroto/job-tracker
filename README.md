# Job Application Tracker

A full-stack web application for tracking a job search: the companies you're
interested in, the jobs they post, the applications you submit, and the people
you meet along the way. Includes a dashboard with statistics and a **Job Match**
feature that ranks jobs by how well they match your skills.

**Stack:** Python 3 · Flask · MySQL 8 · HTML/CSS (no frameworks)

## Features

| Page | What it does |
|------|--------------|
| **Dashboard** | Counts for every table, applications by status, response rate, active applications, most-applied-to companies, recent applications |
| **Companies** | List, detail (with that company's jobs and contacts), add, edit, delete |
| **Jobs** | List, detail, add, edit, delete. Requirements (required/preferred skills, education, experience, remote) are stored in a **JSON** column |
| **Applications** | List with status filter, detail, add, edit, delete. Interview notes (rounds, interviewers, feedback, rating…) are stored in a **JSON** column |
| **Contacts** | List, detail, add, edit, delete |
| **Job Match** | Enter your skills → jobs ranked by match % with matched / missing skills shown |

All forms validate input server-side (required fields, URL/email format,
salary min ≤ max, rating 1–5, valid dates) and every delete asks for
confirmation. Deleting a company cascades to its jobs, applications and
contacts (foreign keys with `ON DELETE CASCADE`).

## Project structure

```
job_tracker/
├── app.py              # Flask routes, form validation, Job Match algorithm
├── database.py         # MySQL connection + all SQL (CRUD functions, dashboard stats)
├── schema.sql          # Creates the database, 4 tables, indexes and sample data
├── requirements.txt    # Python dependencies
├── templates/          # Jinja2 HTML templates (base + one list/form/detail per table)
├── static/style.css    # Stylesheet
├── AI_USAGE.md         # GenAI usage documentation
└── README.md
```

## Setup (fresh clone)

### 1. Prerequisites
- Python 3.9 or newer
- MySQL 8.0 server running locally (MySQL Workbench optional)
- Git

### 2. Clone and install dependencies

```bash
git clone <your-repo-url>
cd job_tracker
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Create the database

Run `schema.sql` once. It drops/creates the `job_tracker` database, creates
the four tables and loads sample data.

```bash
mysql -u root -p < schema.sql
```

Or open `schema.sql` in MySQL Workbench and execute the whole script
(⌘/Ctrl + Shift + Enter).

### 4. Configure the database password

The app reads its connection settings from environment variables (defaults in
parentheses): `DB_HOST` (localhost), `DB_USER` (root), `DB_PASSWORD` (empty),
`DB_NAME` (job_tracker). You only need to set the password:

```bash
# Windows PowerShell
$env:DB_PASSWORD = "your_mysql_password"

# Windows cmd
set DB_PASSWORD=your_mysql_password

# macOS / Linux
export DB_PASSWORD="your_mysql_password"
```

(Alternatively, edit the default in `DB_CONFIG` at the top of `database.py`.)

### 5. Run

```bash
python app.py
```

Open <http://127.0.0.1:5000> in your browser.

## Database schema

```
companies (company_id PK, company_name, industry, website, city, state, notes)
    │
    ├──< jobs (job_id PK, company_id FK, job_title, job_type ENUM, salary_min,
    │          salary_max, job_url, date_posted, requirements JSON)
    │        │
    │        └──< applications (application_id PK, job_id FK, application_date,
    │                           status ENUM, resume_version, cover_letter_sent,
    │                           interview_data JSON)
    │
    └──< contacts (contact_id PK, company_id FK, contact_name, title, email,
                   phone, linkedin_url, notes)
```

Example `requirements` JSON stored on a job:

```json
{"required_skills": ["Python", "SQL", "Flask"],
 "preferred_skills": ["Docker", "AWS"],
 "education": "Bachelor in CS or related field",
 "experience_years": 2,
 "remote_option": true}
```

## How Job Match works

1. The user enters a comma-separated list of skills.
2. For every job that has `required_skills` in its `requirements` JSON, the
   app compares the lists case-insensitively.
3. `match % = matched required skills ÷ total required skills × 100`
4. Jobs are sorted by percentage, and the page shows which skills matched,
   which are missing, and any *preferred* skills the user also has.

Example — skills `Python, SQL, Flask`:

```
1. Software Developer at TechCorp – 100% (3/3 skills)
2. Data Analyst at DataCo – 67% (2/3 skills)   Missing: Tableau
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Access denied for user 'root'@'localhost'` | `DB_PASSWORD` is wrong or not set in the terminal you're running from |
| `Unknown database 'job_tracker'` | Run `schema.sql` (step 3) |
| `ModuleNotFoundError: No module named 'mysql'` | Activate the venv and `pip install -r requirements.txt` |
| `Can't connect to MySQL server` | Make sure the MySQL service is running |
