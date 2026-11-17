-- =====================================================================
-- Job Application Tracker - Database Schema
-- Run this file once to create the database, tables, and sample data:
--     mysql -u root -p < schema.sql
-- or open it in MySQL Workbench and execute the whole script.
-- =====================================================================

DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE job_tracker;

-- ---------------------------------------------------------------------
-- companies
-- ---------------------------------------------------------------------
CREATE TABLE companies (
    company_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry     VARCHAR(50),
    website      VARCHAR(200),
    city         VARCHAR(50),
    state        VARCHAR(50),
    notes        TEXT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- jobs  (many jobs -> one company)
-- ---------------------------------------------------------------------
CREATE TABLE jobs (
    job_id       INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT NOT NULL,
    job_title    VARCHAR(100) NOT NULL,
    job_type     ENUM('Full-time', 'Part-time', 'Contract', 'Internship'),
    salary_min   INT,
    salary_max   INT,
    job_url      VARCHAR(300),
    date_posted  DATE,
    requirements JSON,
    CONSTRAINT fk_jobs_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_salary CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- applications  (many applications -> one job)
-- ---------------------------------------------------------------------
CREATE TABLE applications (
    application_id    INT PRIMARY KEY AUTO_INCREMENT,
    job_id            INT NOT NULL,
    application_date  DATE NOT NULL,
    status            ENUM('Applied', 'Screening', 'Interview', 'Offer', 'Rejected', 'Withdrawn')
                      NOT NULL DEFAULT 'Applied',
    resume_version    VARCHAR(50),
    cover_letter_sent BOOLEAN NOT NULL DEFAULT FALSE,
    interview_data    JSON,
    CONSTRAINT fk_applications_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- contacts  (many contacts -> one company)
-- ---------------------------------------------------------------------
CREATE TABLE contacts (
    contact_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    title        VARCHAR(100),
    email        VARCHAR(100),
    phone        VARCHAR(20),
    linkedin_url VARCHAR(200),
    notes        TEXT,
    CONSTRAINT fk_contacts_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Indexes on foreign keys / common filters
CREATE INDEX idx_jobs_company        ON jobs(company_id);
CREATE INDEX idx_applications_job    ON applications(job_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_contacts_company    ON contacts(company_id);

-- =====================================================================
-- Sample data
-- =====================================================================
INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('Cisco',     'Networking',          'https://www.cisco.com',     'San Jose',  'CA', 'Networking and security leader; strong internship and new-grad programs.'),
('Amazon',    'Technology / Retail', 'https://www.amazon.jobs',   'Seattle',   'WA', 'Huge volume of SDE and data roles; online assessment first.'),
('Microsoft', 'Technology',          'https://careers.microsoft.com', 'Redmond', 'WA', 'Interested in Azure data and SQL Server teams.'),
('Sony',      'Electronics / Gaming','https://www.sony.com/en/SonyInfo/Careers/', 'San Mateo', 'CA', 'PlayStation and Sony Electronics both hire software roles.'),
('Logitech',  'Hardware',            'https://www.logitech.com/careers', 'Newark', 'CA', 'Smaller company; software roles for devices and apps.'),
('Samsung',   'Electronics',         'https://www.samsung.com/us/careers/', 'Mountain View', 'CA', 'Samsung Research America; data and backend positions.');

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Developer',      'Full-time',  70000,  90000, 'https://www.techcorp.com/jobs/101', '2025-01-15',
 '{"required_skills": ["Python", "SQL", "Flask"], "preferred_skills": ["Docker", "AWS"], "education": "Bachelor in CS or related field", "experience_years": 2, "remote_option": true}'),
(2, 'Data Analyst',            'Full-time',  60000,  75000, 'https://www.dataco.io/careers/7',   '2025-01-20',
 '{"required_skills": ["SQL", "Python", "Tableau"], "preferred_skills": ["R", "Excel"], "education": "Bachelor degree", "experience_years": 1, "remote_option": false}'),
(3, 'Backend Engineer',        'Full-time',  95000, 125000, 'https://cloudnine.dev/jobs/be-1',   '2025-02-01',
 '{"required_skills": ["Python", "Flask", "Docker", "AWS"], "preferred_skills": ["Kubernetes", "PostgreSQL"], "education": "Bachelor degree or equivalent experience", "experience_years": 3, "remote_option": true}'),
(4, 'Database Administrator',  'Full-time',  85000, 110000, 'https://www.finserve.com/careers/dba', '2025-02-05',
 '{"required_skills": ["SQL", "MySQL", "Linux"], "preferred_skills": ["Python", "Oracle"], "education": "Bachelor degree", "experience_years": 4, "remote_option": false}'),
(5, 'Junior Web Developer',    'Internship', 20000,  25000, 'https://www.healthbridge.org/jobs/12', '2025-02-10',
 '{"required_skills": ["HTML", "CSS", "JavaScript"], "preferred_skills": ["Python", "Flask"], "education": "Currently enrolled", "experience_years": 0, "remote_option": false}'),
(6, 'Data Engineer',           'Contract',   80000, 100000, 'https://greengrid.energy/jobs/de-3', '2025-02-12',
 '{"required_skills": ["Python", "SQL", "Spark"], "preferred_skills": ["Airflow", "AWS"], "education": "Bachelor degree", "experience_years": 2, "remote_option": true}'),
(1, 'QA Automation Engineer',  'Part-time',  40000,  55000, 'https://www.techcorp.com/jobs/118', '2025-02-18',
 '{"required_skills": ["Python", "Selenium"], "preferred_skills": ["SQL", "Git"], "education": "Associate degree", "experience_years": 1, "remote_option": true}'),
(3, 'Cloud Support Specialist','Full-time',  55000,  70000, 'https://cloudnine.dev/jobs/cs-4',   '2025-02-20',
 '{"required_skills": ["Linux", "AWS", "Networking"], "preferred_skills": ["Python"], "education": "Associate degree", "experience_years": 1, "remote_option": true}');

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, '2025-01-18', 'Interview', 'v2-developer',  TRUE,
 '{"interview_rounds": 2, "interviewers": ["Sarah Johnson", "Mike Chen"], "technical_questions": ["SQL joins", "Python basics", "API design"], "feedback": "Strong technical skills, good communication", "next_steps": "Final round scheduled"}'),
(2, '2025-01-22', 'Screening', 'v1-analyst',    FALSE, NULL),
(3, '2025-02-03', 'Applied',   'v2-developer',  TRUE,  NULL),
(4, '2025-02-06', 'Rejected',  'v1-general',    FALSE,
 '{"interview_rounds": 1, "interviewers": ["Emily Williams"], "technical_questions": ["Database normalization", "Transaction isolation"], "feedback": "Needs more experience with cloud platforms", "rating": 3}'),
(5, '2025-02-11', 'Offer',     'v1-general',    TRUE,
 '{"interview_rounds": 1, "interviewers": ["Tom Alvarez"], "feedback": "Great culture fit", "next_steps": "Offer extended", "offer_amount": 24000}'),
(6, '2025-02-14', 'Applied',   'v3-data',       TRUE,  NULL),
(7, '2025-02-19', 'Withdrawn', 'v2-developer',  FALSE, NULL),
(1, '2025-02-25', 'Applied',   'v3-data',       FALSE, NULL);

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 'Sarah Johnson',  'Engineering Manager',  'sarah.johnson@cisco.com',     '408-555-0101', 'https://linkedin.com/in/sarahjohnson', 'Led my first-round interview.'),
(1, 'Mike Chen',      'Senior Developer',     'mike.chen@cisco.com',         '408-555-0102', 'https://linkedin.com/in/mikechen',     'Technical interviewer, very friendly.'),
(2, 'Priya Patel',    'Technical Recruiter',  'priya.patel@amazon.com',      '206-555-0199', 'https://linkedin.com/in/priyapatel',   'Reached out via LinkedIn.'),
(3, 'Alex Rivera',    'Principal Engineer',   'alex.rivera@microsoft.com',   '425-555-0150', 'https://linkedin.com/in/alexrivera',   'Met at a campus tech talk.'),
(4, 'Emily Williams', 'Database Team Lead',   'emily.williams@sony.com',     '650-555-0177', NULL,                                   'Interviewed me for the DBA role.'),
(5, 'Tom Alvarez',    'IT Director',          'tom.alvarez@logitech.com',    '510-555-0133', 'https://linkedin.com/in/tomalvarez',   'Extended the internship offer.');
