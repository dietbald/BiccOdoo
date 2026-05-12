# 002_sms_followup_email_blast

## What changes

Adds two things:

1. A manual server action **"BICC v5: Send SMS Queue Digest"** on
   `hr.applicant`.
2. A menu item **Recruitment → Reporting → SMS Follow-up Queue** that
   fires the same server action.

The server action is also bound to the hr.applicant Action menu (gear
icon) on form + list views, so HR has two entry points.

## What the digest looks like

When triggered, the action emails the HR Recruitment Manager group **one**
digest. The body is grouped **by job position** — each job renders as its
own H3 + 3-column table:

| Column | Content |
|---|---|
| Applicant | Candidate name, hyperlinked to their hr.applicant record |
| Mobile | `partner_phone`, or `(no phone on file)` |
| SMS to send | The exact SMS text, ready to copy-paste, with company short name + first name + job role pre-filled |

Job sections appear in alphabetical order. The `(No job position)` catch-all
section sorts to the end (the leading `(` puts it after letters).

## Which applicants get listed

| Queue | Stage | Filter | SMS wording |
|---|---|---|---|
| Qualification | 2 | `x_studio_reminder_date != null` AND `x_studio_sms_reminder_date == null` | "We sent you the Applicant Information form…" |
| Resume Missing | 1 | `x_studio_resume_request_date != null` AND `x_studio_sms_new_reminder_date == null` AND `attachment_number == 0` | "…didn't see a resume attached. Could you reply to our email with it?" |
| Assessment | 7 | `x_studio_assessment_final_reminder_date != null` | "Have you had a chance to do the assessment we emailed you…?" |

Within a single job table, an applicant can appear once — the queue they
sit in determines which SMS wording is rendered in their row.

## Behaviour

- **One email, not many.** HR receives a single digest in their inbox;
  nothing is sent to the applicants themselves.
- **Manual SMS workflow preserved.** HR copies the SMS Text column into
  their phone, texts the matching number, and then sets the SMS reminder
  date field on the applicant record so the queue clears.
- **Defensive on missing fields.** Each queue field-checks at runtime, so
  the action is safe to deploy before all v5 reminder-field blocks land
  — queues whose driving field is missing are simply omitted from the
  digest (no error).
- **No data mutations.** No `x_studio_sms_*_date` is stamped; no applicant
  is emailed; pure read + render + notify-HR.
- **Blast across DB.** Even when triggered from a single applicant's form
  view, the action sweeps the whole DB. The Action-menu binding is a
  convenience entry point, not a per-record scope.

## QA on dev

1. Open dev Odoo as a recruiter once `deploy-dev` finishes.
2. Recruitment → Reporting → **SMS Follow-up Queue** menu item should appear.
3. Recruitment → Applicants → gear icon on any applicant → confirm
   *BICC v5: Send SMS Queue Digest* shows up.
4. Click either entry point. The bottom-of-action `log()` line reports
   total candidates and number of job sections.
5. Check the HR Recruitment Manager group's inbox — one email with a
   subject like `BICC SMS Queue: N candidate(s) need a follow-up SMS`
   and one table per job position inside.
6. Verify each applicant link deep-links to the correct hr.applicant
   record.
7. Verify the SMS text column shows the right wording per queue
   (Qualification / Resume Missing / Assessment).
8. On dev DBs that don't yet have v5 reminder fields, the action should
   log `queue is empty` and send nothing.

## Implementation notes

- **No closures.** Odoo SaaS safe_eval rejects `LOAD_CLOSURE` and
  `MAKE_CELL` opcodes. The script is pure procedural: no nested `def`,
  no generator expressions / list comprehensions that capture outer-scope
  variables. The first dev deploy failed precisely on this rule before
  the rewrite.
- **HTML email body** is sent via `mail.mail.sudo().create({body_html:
  ...}).send()` — `message_notify` / `message_post` escape HTML in SaaS
  safe_eval and would render the tables as plain text.
- **Job grouping** uses a plain `dict` keyed by `job_id.name`; sort is
  alphabetical via `list.sort()`. `(No job position)` is the catch-all
  for applicants whose `job_id` is empty.
- **Menu under Reporting**: parent xml_id `hr_recruitment.report_hr_recruitment`
  was looked up from the production baseline export and verified —
  Recruitment → Reporting with sequence 99.
