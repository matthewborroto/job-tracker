# AI Usage Documentation

## Tools Used

- **Claude (Anthropic)** — used to assist with the project. Claude
  generated the initial versions of the files in this repository
  (`schema.sql`, `database.py`, `app.py`, the templates, `style.css`,
  `README.md`) from the project specification. I made any modifications and 
  then tested them.

## Key Prompts

These are the prompts (paraphrased where long) that drove the project:
1. *"Compare MongoDB and MySQL for storing user profiles with varying fields
   *"Explain when I should use a JSON column vs a separate table"
   — from Assignments 7 and 8; this is why `requirements` and
   `interview_data` are JSON columns instead of extra tables.
2. *"Write a Flask route to display all jobs with company names using JOIN"* —
   the pattern used for every list page (`get_all_jobs`,
   `get_all_applications`, `get_all_contacts` in `database.py`).
3. *"How do I update just one field inside a JSON column without replacing the
   entire object?"* — led to the `merge_json()` helper so editing an
   application doesn't wipe JSON keys the form doesn't show (like
   `technical_questions`).

## What Worked Well

- **Boilerplate CRUD.** Claude produced the repetitive add/edit/delete routes
  and forms for all four tables in one pass, which would have taken me hours.
- **Schema accuracy.** Because I attached the specification, the generated
  `schema.sql` used the exact column names, ENUM values and JSON columns the
  rubric asks for, plus foreign keys with `ON DELETE CASCADE` and indexes.
- **Job Match algorithm.** The `calculate_matches()` function is short, easy
  to read, and the output matches the example in the spec
  (`Data Analyst – 67% (2/3 skills), Missing: Tableau`).
- **Testing.** Claude wrote a throwaway test script that hit every route
  (GET and POST, valid and invalid input, deletes and cascades) before I 
  ran the app, which caught problems early.
- **Explanations.** Asking *why* (e.g. why `->>` instead of `->`, why the
  JSON data is parsed in Python instead of with `JSON_EXTRACT`) helped me
  understand the code instead of just pasting it.

## What I Modified

- Restyled the color scheme in `style.css` — changed the `--primary` CSS variables
- Replaced placeholder sample data (TechCorp, DataCo…) in `schema.sql` with
  companies I'm actually interested in, so the demo reflects my real job search.
- Fixed the response-rate calculation. The AI counted "Withdrawn" applications as responses.
  I excluded them in `get_dashboard_stats()` since withdrawing is my action, not the employer's.

## Lessons Learned

- **AI output was tested on my machine.** The code was originally tested
  against a stand-in database. Environment variables,
  passwords and the MySQL service are my responsibility.
- **Ask for the reasoning, not just the code.** The most useful answers were
  the ones where I asked *why* a choice was made (JSON column vs. table,
  cascading deletes, where validation lives).
- **AI is fast at boilerplate and weaker at judgment calls.** It will happily
  generate ten near-identical routes. Deciding what the app actually needs
  (which stats matter, what validation is reasonable) was still up to me.
