"""
database.py - All database access for the Job Application Tracker.

Connection settings come from environment variables so no password has to be
committed to GitHub. Defaults are used if the variables are not set:

    DB_HOST      (default: localhost)
    DB_USER      (default: root)
    DB_PASSWORD  (default: empty string)  <-- set this!
    DB_NAME      (default: job_tracker)

Example (Windows PowerShell):   $env:DB_PASSWORD = "mypassword"
Example (macOS / Linux):        export DB_PASSWORD="mypassword"
"""

import json
import os

import mysql.connector

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "job_tracker"),
}


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def get_connection():
    """Open and return a new MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)


def query(sql, params=None, one=False):
    """Run a SELECT and return rows as dictionaries (or a single row)."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
        cursor.close()
    finally:
        conn.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, params=None):
    """Run an INSERT / UPDATE / DELETE, commit, and return lastrowid."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
    finally:
        conn.close()
    return last_id


def parse_json(value):
    """MySQL returns JSON columns as str (or bytes); turn them into Python objects."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def to_json(value):
    """Serialize a Python object for storage in a JSON column (None stays NULL)."""
    return json.dumps(value) if value is not None else None


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------
def get_all_companies():
    return query(
        """
        SELECT c.*,
               (SELECT COUNT(*) FROM jobs j WHERE j.company_id = c.company_id)     AS job_count,
               (SELECT COUNT(*) FROM contacts t WHERE t.company_id = c.company_id) AS contact_count
        FROM companies c
        ORDER BY c.company_name
        """
    )


def get_company(company_id):
    return query("SELECT * FROM companies WHERE company_id = %s", (company_id,), one=True)


def add_company(data):
    return execute(
        """
        INSERT INTO companies (company_name, industry, website, city, state, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (data["company_name"], data["industry"], data["website"],
         data["city"], data["state"], data["notes"]),
    )


def update_company(company_id, data):
    execute(
        """
        UPDATE companies
        SET company_name = %s, industry = %s, website = %s, city = %s, state = %s, notes = %s
        WHERE company_id = %s
        """,
        (data["company_name"], data["industry"], data["website"],
         data["city"], data["state"], data["notes"], company_id),
    )


def delete_company(company_id):
    execute("DELETE FROM companies WHERE company_id = %s", (company_id,))


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]


def _hydrate_job(row):
    if row:
        row["requirements"] = parse_json(row.get("requirements"))
    return row


def get_all_jobs():
    rows = query(
        """
        SELECT j.*, c.company_name,
               (SELECT COUNT(*) FROM applications a WHERE a.job_id = j.job_id) AS application_count
        FROM jobs j
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY j.date_posted DESC, j.job_id DESC
        """
    )
    return [_hydrate_job(r) for r in rows]


def get_job(job_id):
    row = query(
        """
        SELECT j.*, c.company_name
        FROM jobs j
        JOIN companies c ON j.company_id = c.company_id
        WHERE j.job_id = %s
        """,
        (job_id,),
        one=True,
    )
    return _hydrate_job(row)


def get_jobs_for_company(company_id):
    rows = query(
        "SELECT * FROM jobs WHERE company_id = %s ORDER BY date_posted DESC", (company_id,)
    )
    return [_hydrate_job(r) for r in rows]


def add_job(data):
    return execute(
        """
        INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max,
                          job_url, date_posted, requirements)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (data["company_id"], data["job_title"], data["job_type"], data["salary_min"],
         data["salary_max"], data["job_url"], data["date_posted"], to_json(data["requirements"])),
    )


def update_job(job_id, data):
    execute(
        """
        UPDATE jobs
        SET company_id = %s, job_title = %s, job_type = %s, salary_min = %s, salary_max = %s,
            job_url = %s, date_posted = %s, requirements = %s
        WHERE job_id = %s
        """,
        (data["company_id"], data["job_title"], data["job_type"], data["salary_min"],
         data["salary_max"], data["job_url"], data["date_posted"], to_json(data["requirements"]),
         job_id),
    )


def delete_job(job_id):
    execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]


def _hydrate_application(row):
    if row:
        row["interview_data"] = parse_json(row.get("interview_data"))
        row["cover_letter_sent"] = bool(row.get("cover_letter_sent"))
    return row


def get_all_applications():
    rows = query(
        """
        SELECT a.*, j.job_title, c.company_name, c.company_id
        FROM applications a
        JOIN jobs j      ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY a.application_date DESC, a.application_id DESC
        """
    )
    return [_hydrate_application(r) for r in rows]


def get_application(application_id):
    row = query(
        """
        SELECT a.*, j.job_title, c.company_name, c.company_id
        FROM applications a
        JOIN jobs j      ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        WHERE a.application_id = %s
        """,
        (application_id,),
        one=True,
    )
    return _hydrate_application(row)


def get_applications_for_job(job_id):
    rows = query(
        "SELECT * FROM applications WHERE job_id = %s ORDER BY application_date DESC", (job_id,)
    )
    return [_hydrate_application(r) for r in rows]


def add_application(data):
    return execute(
        """
        INSERT INTO applications (job_id, application_date, status, resume_version,
                                  cover_letter_sent, interview_data)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (data["job_id"], data["application_date"], data["status"], data["resume_version"],
         data["cover_letter_sent"], to_json(data["interview_data"])),
    )


def update_application(application_id, data):
    execute(
        """
        UPDATE applications
        SET job_id = %s, application_date = %s, status = %s, resume_version = %s,
            cover_letter_sent = %s, interview_data = %s
        WHERE application_id = %s
        """,
        (data["job_id"], data["application_date"], data["status"], data["resume_version"],
         data["cover_letter_sent"], to_json(data["interview_data"]), application_id),
    )


def delete_application(application_id):
    execute("DELETE FROM applications WHERE application_id = %s", (application_id,))


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------
def get_all_contacts():
    return query(
        """
        SELECT t.*, c.company_name
        FROM contacts t
        JOIN companies c ON t.company_id = c.company_id
        ORDER BY t.contact_name
        """
    )


def get_contact(contact_id):
    return query(
        """
        SELECT t.*, c.company_name
        FROM contacts t
        JOIN companies c ON t.company_id = c.company_id
        WHERE t.contact_id = %s
        """,
        (contact_id,),
        one=True,
    )


def get_contacts_for_company(company_id):
    return query(
        "SELECT * FROM contacts WHERE company_id = %s ORDER BY contact_name", (company_id,)
    )


def add_contact(data):
    return execute(
        """
        INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (data["company_id"], data["contact_name"], data["title"], data["email"],
         data["phone"], data["linkedin_url"], data["notes"]),
    )


def update_contact(contact_id, data):
    execute(
        """
        UPDATE contacts
        SET company_id = %s, contact_name = %s, title = %s, email = %s, phone = %s,
            linkedin_url = %s, notes = %s
        WHERE contact_id = %s
        """,
        (data["company_id"], data["contact_name"], data["title"], data["email"],
         data["phone"], data["linkedin_url"], data["notes"], contact_id),
    )


def delete_contact(contact_id):
    execute("DELETE FROM contacts WHERE contact_id = %s", (contact_id,))


# ---------------------------------------------------------------------------
# Dashboard statistics
# ---------------------------------------------------------------------------
def get_dashboard_stats():
    counts = query(
        """
        SELECT
            (SELECT COUNT(*) FROM companies)    AS companies,
            (SELECT COUNT(*) FROM jobs)         AS jobs,
            (SELECT COUNT(*) FROM applications) AS applications,
            (SELECT COUNT(*) FROM contacts)     AS contacts
        """,
        one=True,
    )

    status_rows = query(
        "SELECT status, COUNT(*) AS count FROM applications GROUP BY status"
    )
    by_status = {s: 0 for s in STATUSES}
    for r in status_rows:
        by_status[r["status"]] = r["count"]

    total = counts["applications"] or 0
    responded = sum(v for k, v in by_status.items() if k not in ("Applied", "Withdrawn"))
    response_rate = round(responded * 100.0 / total, 1) if total else 0.0

    active = by_status["Applied"] + by_status["Screening"] + by_status["Interview"]

    recent = query(
        """
        SELECT a.application_id, a.application_date, a.status, j.job_title, c.company_name
        FROM applications a
        JOIN jobs j      ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY a.application_date DESC, a.application_id DESC
        LIMIT 5
        """
    )

    top_companies = query(
        """
        SELECT c.company_name, COUNT(a.application_id) AS application_count
        FROM companies c
        JOIN jobs j         ON j.company_id = c.company_id
        JOIN applications a ON a.job_id = j.job_id
        GROUP BY c.company_id, c.company_name
        ORDER BY application_count DESC, c.company_name
        LIMIT 5
        """
    )

    return {
        "counts": counts,
        "by_status": by_status,
        "response_rate": response_rate,
        "active": active,
        "offers": by_status["Offer"],
        "recent": recent,
        "top_companies": top_companies,
    }
