# AI Usage Documentation

> **Note to self before submitting:** this file was drafted with Claude's help.
> Everything in it is accurate as of the first draft, but I need to update the
> *What I Modified* and *Lessons Learned* sections as I test the app on my own
> machine and make my own changes.

## Tools Used

- **Claude (Anthropic)** — used throughout the course inside the Claude app
  for the zyBooks assignments and for this project. For the project, Claude
  generated the initial versions of every file in this repository
  (`schema.sql`, `database.py`, `app.py`, the templates, `style.css`,
  `README.md`) from the project specification, and tested them.

## Key Prompts

These are the prompts (paraphrased where long) that drove the project:
1. *"Compare MongoDB and MySQL for storing user profiles with varying fields
   *"Explain when I should use a JSON column vs a separate table"
   — from Assignments 7 and 8; this is why `requirements` and
   `interview_data` are JSON columns instead of extra tables.
2. *"Write a Flask route to display all jobs with company names using JOIN"* —
   the pattern used for every list page (`get_all_jobs`,
   `get_all_applications`, `get_all_contacts` in `database.py`).
3. *"Create a function to calculate skill match percentage"* — produced
   `calculate_matches()` in `app.py`.
4. *"How do I update just one field inside a JSON column without replacing the
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
  (GET and POST, valid and invalid input, deletes and cascades) before I ever
  ran the app, which caught problems early.
- **Explanations.** Asking *why* (e.g. why `->>` instead of `->`, why the
  JSON data is parsed in Python instead of with `JSON_EXTRACT`) helped me
  understand the code instead of just pasting it.

## What I Modified

`[Be honest here — the grader wants to see your own judgment. Fill in as you go.
Examples of the kind of thing to record:]`

- `[Changed the default DB_CONFIG / added my own .env handling]`
- `[Adjusted the colors / layout in style.css to my taste]`
- `[Changed sample data in schema.sql to real companies I've applied to]`
- `[Fixed a bug I found when running it: ...]`
- `[Added/removed a dashboard statistic]`
- `[Renamed something or simplified code I didn't fully understand]`

## Lessons Learned

- **Give the AI the real spec, not a summary.** Attaching the actual
  specification document produced a schema that matched the rubric
  column-for-column; earlier in the course, summarizing a question in my own
  words sometimes produced answers that were technically right but didn't
  match what the grader expected.
- **AI output still has to be tested on *my* machine.** The code was tested
  against a stand-in database, not my MySQL install — environment variables,
  passwords and the MySQL service are my responsibility.
  `[Add anything that broke on first run and how you fixed it.]`
- **Ask for the reasoning, not just the code.** The most useful answers were
  the ones where I asked *why* a choice was made (JSON column vs. table,
  cascading deletes, where validation lives). That's what let me answer the
  quiz questions and would let me explain this code in an interview.
- **AI is fast at boilerplate and weaker at judgment calls.** It will happily
  generate ten near-identical routes; deciding what the app actually needs
  (which stats matter, what validation is reasonable) was still up to me.
- `[Your own takeaway]`
