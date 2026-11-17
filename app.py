"""
app.py - Job Application Tracker (Flask)

Run with:   python app.py
Then open:  http://127.0.0.1:5000
"""

import os
import re
from datetime import date

from flask import Flask, abort, flash, redirect, render_template, request, url_for

import database as db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def clean(value):
    """Strip whitespace and convert empty strings to None (stored as NULL)."""
    value = (value or "").strip()
    return value or None


def to_int(value):
    """Convert a form value to int; returns None for blank, raises ValueError if invalid."""
    value = (value or "").strip()
    return int(value) if value else None


def split_list(value):
    """'Python, SQL,Flask' -> ['Python', 'SQL', 'Flask'] (de-duplicated, order kept)."""
    seen, result = set(), []
    for item in re.split(r"[,\n;]+", value or ""):
        item = item.strip()
        if item and item.lower() not in seen:
            seen.add(item.lower())
            result.append(item)
    return result


def merge_json(existing, updated):
    """
    Keep JSON keys the edit form doesn't expose (e.g. 'technical_questions',
    'offer_amount') when a record is updated. Returns None if both are empty.
    """
    if updated is None:
        return None
    merged = dict(existing) if isinstance(existing, dict) else {}
    merged.update(updated)
    return merged


def is_valid_url(value):
    return value is None or re.match(r"^https?://", value, re.IGNORECASE) is not None


def is_valid_email(value):
    return value is None or re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value) is not None


def is_valid_date(value):
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


@app.context_processor
def inject_globals():
    return {"today": date.today().isoformat()}


@app.template_filter("money")
def money(value):
    return f"${value:,.0f}" if value is not None else "—"


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/")
def dashboard():
    stats = db.get_dashboard_stats()
    return render_template("dashboard.html", stats=stats, statuses=db.STATUSES)


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------
def company_form_data(form):
    data = {
        "company_name": clean(form.get("company_name")),
        "industry": clean(form.get("industry")),
        "website": clean(form.get("website")),
        "city": clean(form.get("city")),
        "state": clean(form.get("state")),
        "notes": clean(form.get("notes")),
    }
    errors = []
    if not data["company_name"]:
        errors.append("Company name is required.")
    if not is_valid_url(data["website"]):
        errors.append("Website must start with http:// or https://.")
    return data, errors


@app.route("/companies")
def companies():
    return render_template("companies.html", companies=db.get_all_companies())


@app.route("/companies/<int:company_id>")
def company_detail(company_id):
    company = db.get_company(company_id) or abort(404)
    return render_template(
        "company_detail.html",
        company=company,
        jobs=db.get_jobs_for_company(company_id),
        contacts=db.get_contacts_for_company(company_id),
    )


@app.route("/companies/add", methods=["GET", "POST"])
def add_company():
    if request.method == "POST":
        data, errors = company_form_data(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("company_form.html", company=data, action="Add")
        new_id = db.add_company(data)
        flash(f"Company '{data['company_name']}' added.", "success")
        return redirect(url_for("company_detail", company_id=new_id))
    return render_template("company_form.html", company={}, action="Add")


@app.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
def edit_company(company_id):
    company = db.get_company(company_id) or abort(404)
    if request.method == "POST":
        data, errors = company_form_data(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            data["company_id"] = company_id
            return render_template("company_form.html", company=data, action="Edit")
        db.update_company(company_id, data)
        flash("Company updated.", "success")
        return redirect(url_for("company_detail", company_id=company_id))
    return render_template("company_form.html", company=company, action="Edit")


@app.route("/companies/<int:company_id>/delete", methods=["POST"])
def delete_company(company_id):
    company = db.get_company(company_id) or abort(404)
    db.delete_company(company_id)
    flash(f"Company '{company['company_name']}' and its jobs, applications and contacts were deleted.", "success")
    return redirect(url_for("companies"))


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
def job_form_data(form):
    errors = []
    try:
        salary_min = to_int(form.get("salary_min"))
        salary_max = to_int(form.get("salary_max"))
    except ValueError:
        salary_min = salary_max = None
        errors.append("Salary values must be whole numbers.")
    try:
        experience_years = to_int(form.get("experience_years"))
    except ValueError:
        experience_years = None
        errors.append("Experience years must be a whole number.")

    required_skills = split_list(form.get("required_skills"))
    preferred_skills = split_list(form.get("preferred_skills"))
    education = clean(form.get("education"))
    remote_option = form.get("remote_option") == "on"

    # Only store a requirements object if the user filled in something
    requirements = None
    if required_skills or preferred_skills or education or experience_years is not None or remote_option:
        requirements = {
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "education": education,
            "experience_years": experience_years,
            "remote_option": remote_option,
        }

    data = {
        "company_id": to_int(form.get("company_id")) if (form.get("company_id") or "").isdigit() else None,
        "job_title": clean(form.get("job_title")),
        "job_type": clean(form.get("job_type")),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "job_url": clean(form.get("job_url")),
        "date_posted": clean(form.get("date_posted")),
        "requirements": requirements,
    }

    if not data["company_id"]:
        errors.append("Please choose a company.")
    if not data["job_title"]:
        errors.append("Job title is required.")
    if data["job_type"] and data["job_type"] not in db.JOB_TYPES:
        errors.append("Invalid job type.")
    if salary_min is not None and salary_min < 0 or salary_max is not None and salary_max < 0:
        errors.append("Salary cannot be negative.")
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        errors.append("Minimum salary cannot be greater than maximum salary.")
    if not is_valid_url(data["job_url"]):
        errors.append("Job URL must start with http:// or https://.")
    if data["date_posted"] and not is_valid_date(data["date_posted"]):
        errors.append("Date posted must be a valid date (YYYY-MM-DD).")
    if experience_years is not None and experience_years < 0:
        errors.append("Experience years cannot be negative.")
    return data, errors


def job_form_view(job, action):
    """Render the job form, flattening the requirements JSON into form fields."""
    req = job.get("requirements") or {}
    form_values = dict(job)
    form_values.update({
        "required_skills": ", ".join(req.get("required_skills") or []),
        "preferred_skills": ", ".join(req.get("preferred_skills") or []),
        "education": req.get("education") or "",
        "experience_years": req.get("experience_years") if req.get("experience_years") is not None else "",
        "remote_option": bool(req.get("remote_option")),
    })
    return render_template(
        "job_form.html",
        job=form_values,
        action=action,
        companies=db.get_all_companies(),
        job_types=db.JOB_TYPES,
    )


@app.route("/jobs")
def jobs():
    return render_template("jobs.html", jobs=db.get_all_jobs())


@app.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = db.get_job(job_id) or abort(404)
    return render_template(
        "job_detail.html", job=job, applications=db.get_applications_for_job(job_id)
    )


@app.route("/jobs/add", methods=["GET", "POST"])
def add_job():
    if request.method == "POST":
        data, errors = job_form_data(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return job_form_view(data, "Add")
        new_id = db.add_job(data)
        flash(f"Job '{data['job_title']}' added.", "success")
        return redirect(url_for("job_detail", job_id=new_id))
    preset = {"company_id": request.args.get("company_id", type=int), "date_posted": date.today().isoformat()}
    return job_form_view(preset, "Add")


@app.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
def edit_job(job_id):
    job = db.get_job(job_id) or abort(404)
    if request.method == "POST":
        data, errors = job_form_data(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            data["job_id"] = job_id
            return job_form_view(data, "Edit")
        data["requirements"] = merge_json(job.get("requirements"), data["requirements"])
        db.update_job(job_id, data)
        flash("Job updated.", "success")
        return redirect(url_for("job_detail", job_id=job_id))
    return job_form_view(job, "Edit")


@app.route("/jobs/<int:job_id>/delete", methods=["POST"])
def delete_job(job_id):
    job = db.get_job(job_id) or abort(404)
    db.delete_job(job_id)
    flash(f"Job '{job['job_title']}' and its applications were deleted.", "success")
    return redirect(url_for("jobs"))


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
def application_form_data(form):
    errors = []
    try:
        interview_rounds = to_int(form.get("interview_rounds"))
        rating = to_int(form.get("rating"))
    except ValueError:
        interview_rounds = rating = None
        errors.append("Interview rounds and rating must be whole numbers.")

    interviewers = split_list(form.get("interviewers"))
    feedback = clean(form.get("feedback"))
    next_steps = clean(form.get("next_steps"))

    interview_data = None
    if interview_rounds is not None or interviewers or feedback or next_steps or rating is not None:
        interview_data = {
            "interview_rounds": interview_rounds,
            "interviewers": interviewers,
            "feedback": feedback,
            "next_steps": next_steps,
            "rating": rating,
        }

    data = {
        "job_id": to_int(form.get("job_id")) if (form.get("job_id") or "").isdigit() else None,
        "application_date": clean(form.get("application_date")),
        "status": clean(form.get("status")) or "Applied",
        "resume_version": clean(form.get("resume_version")),
        "cover_letter_sent": form.get("cover_letter_sent") == "on",
        "interview_data": interview_data,
    }

    if not data["job_id"]:
        errors.append("Please choose a job.")
    if not data["application_date"]:
        errors.append("Application date is required.")
    elif not is_valid_date(data["application_date"]):
        errors.append("Application date must be a valid date (YYYY-MM-DD).")
    if data["status"] not in db.STATUSES:
        errors.append("Invalid status.")
    if rating is not None and not 1 <= rating <= 5:
        errors.append("Rating must be between 1 and 5.")
    if interview_rounds is not None and interview_rounds < 0:
        errors.append("Interview rounds cannot be negative.")
    return data, errors


def application_form_view(application, action):
    iv = application.get("interview_data") or {}
    form_values = dict(application)
    form_values.update({
        "interview_rounds": iv.get("interview_rounds") if iv.get("interview_rounds") is not None else "",
        "interviewers": ", ".join(iv.get("interviewers") or []),
        "feedback": iv.get("feedback") or "",
        "next_steps": iv.get("next_steps") or "",
        "rating": iv.get("rating") if iv.get("rating") is not None else "",
    })
    return render_template(
        "application_form.html",
        application=form_values,
        action=action,
        jobs=db.get_all_jobs(),
        statuses=db.STATUSES,
    )


@app.route("/applications")
def applications():
    status_filter = request.args.get("status")
    all_apps = db.get_all_applications()
    if status_filter in db.STATUSES:
        all_apps = [a for a in all_apps if a["status"] == status_filter]
    return render_template(
        "applications.html", applications=all_apps, statuses=db.STATUSES, status_filter=status_filter
    )


@app.route("/applications/<int:application_id>")
def application_detail(application_id):
    application = db.get_application(application_id) or abort(404)
    return render_template("application_detail.html", application=application)


@app.route("/applications/add", methods=["GET", "POST"])
def add_application():
    if request.method == "POST":
        data, errors = application_form_data(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return application_form_view(data, "Add")
        new_id = db.add_application(data)
        flash("Application added.", "success")
        return redirect(url_for("application_detail", application_id=new_id))
    preset = {
        "job_id": request.args.get("job_id", type=int),
        "application_date": date.today().isoformat(),
        "status": "Applied",
    }
    return application_form_view(preset, "Add")


@app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
def edit_application(application_id):
    application = db.get_application(application_id) or abort(404)
    if request.method == "POST":
        data, errors = application_form_data(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            data["application_id"] = application_id
            return application_form_view(data, "Edit")
        data["interview_data"] = merge_json(application.get("interview_data"), data["interview_data"])
        db.update_application(application_id, data)
        flash("Application updated.", "success")
        return redirect(url_for("application_detail", application_id=application_id))
    return application_form_view(application, "Edit")


@app.route("/applications/<int:application_id>/delete", methods=["POST"])
def delete_application(application_id):
    db.get_application(application_id) or abort(404)
    db.delete_application(application_id)
    flash("Application deleted.", "success")
    return redirect(url_for("applications"))


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------
def contact_form_data(form):
    data = {
        "company_id": to_int(form.get("company_id")) if (form.get("company_id") or "").isdigit() else None,
        "contact_name": clean(form.get("contact_name")),
        "title": clean(form.get("title")),
        "email": clean(form.get("email")),
        "phone": clean(form.get("phone")),
        "linkedin_url": clean(form.get("linkedin_url")),
        "notes": clean(form.get("notes")),
    }
    errors = []
    if not data["company_id"]:
        errors.append("Please choose a company.")
    if not data["contact_name"]:
        errors.append("Contact name is required.")
    if not is_valid_email(data["email"]):
        errors.append("Email address is not valid.")
    if not is_valid_url(data["linkedin_url"]):
        errors.append("LinkedIn URL must start with http:// or https://.")
    return data, errors


def contact_form_view(contact, action):
    return render_template(
        "contact_form.html", contact=contact, action=action, companies=db.get_all_companies()
    )


@app.route("/contacts")
def contacts():
    return render_template("contacts.html", contacts=db.get_all_contacts())


@app.route("/contacts/<int:contact_id>")
def contact_detail(contact_id):
    contact = db.get_contact(contact_id) or abort(404)
    return render_template("contact_detail.html", contact=contact)


@app.route("/contacts/add", methods=["GET", "POST"])
def add_contact():
    if request.method == "POST":
        data, errors = contact_form_data(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return contact_form_view(data, "Add")
        new_id = db.add_contact(data)
        flash(f"Contact '{data['contact_name']}' added.", "success")
        return redirect(url_for("contact_detail", contact_id=new_id))
    preset = {"company_id": request.args.get("company_id", type=int)}
    return contact_form_view(preset, "Add")


@app.route("/contacts/<int:contact_id>/edit", methods=["GET", "POST"])
def edit_contact(contact_id):
    contact = db.get_contact(contact_id) or abort(404)
    if request.method == "POST":
        data, errors = contact_form_data(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            data["contact_id"] = contact_id
            return contact_form_view(data, "Edit")
        db.update_contact(contact_id, data)
        flash("Contact updated.", "success")
        return redirect(url_for("contact_detail", contact_id=contact_id))
    return contact_form_view(contact, "Edit")


@app.route("/contacts/<int:contact_id>/delete", methods=["POST"])
def delete_contact(contact_id):
    contact = db.get_contact(contact_id) or abort(404)
    db.delete_contact(contact_id)
    flash(f"Contact '{contact['contact_name']}' deleted.", "success")
    return redirect(url_for("contacts"))


# ---------------------------------------------------------------------------
# Job Match
# ---------------------------------------------------------------------------
def calculate_matches(user_skills, jobs_list):
    """
    Compare the user's skills against each job's required_skills (case-insensitive).

    match % = (required skills the user has) / (total required skills) * 100
    Jobs with no required skills listed are skipped. Results are sorted by
    percentage (desc), then by number of matched skills, then by title.
    """
    user_set = {s.lower() for s in user_skills}
    results = []
    for job in jobs_list:
        req = job.get("requirements") or {}
        required = req.get("required_skills") or []
        if not required:
            continue
        matched = [s for s in required if s.lower() in user_set]
        missing = [s for s in required if s.lower() not in user_set]
        preferred = req.get("preferred_skills") or []
        preferred_matched = [s for s in preferred if s.lower() in user_set]
        percent = round(len(matched) * 100 / len(required))
        results.append({
            "job": job,
            "percent": percent,
            "matched": matched,
            "missing": missing,
            "preferred_matched": preferred_matched,
            "required_total": len(required),
        })
    results.sort(key=lambda r: (-r["percent"], -len(r["matched"]), r["job"]["job_title"]))
    return results


@app.route("/job-match", methods=["GET", "POST"])
def job_match():
    skills_input = ""
    user_skills, results = [], None
    if request.method == "POST":
        skills_input = request.form.get("skills", "")
        user_skills = split_list(skills_input)
        if not user_skills:
            flash("Enter at least one skill, separated by commas.", "error")
        else:
            results = calculate_matches(user_skills, db.get_all_jobs())
    return render_template(
        "job_match.html", skills_input=skills_input, user_skills=user_skills, results=results
    )


# ---------------------------------------------------------------------------
# Error pages
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
