# 002_sms_followup_email_blast

## What changes

Adds a manual server action **"BICC v5: Send SMS Queue Digest"** to the
hr.applicant Action menu (form + list views). When HR triggers it, the
action emails the HR Recruitment Manager group **one** digest listing every
applicant who needs an SMS follow-up right now. Each section is a 3-column
table:

| Column | Content |
|---|---|
| Applicant | Candidate name, hyperlinked to their hr.applicant record |
| Mobile | `partner_phone`, or `(no phone on file)` |
| SMS to send | The exact SMS text, ready to copy-paste, with company short name + first name + job role pre-filled |

Three sections appear, in this order, only if they have rows:

| Section | Stage | Queue criterion |
|---|---|---|
| Qualification &mdash; Info Survey Pending | 2 | `x_studio_reminder_date != null` AND `x_studio_sms_reminder_date == null` |
| Resume Missing | 1 | `x_studio_resume_request_date != null` AND `x_studio_sms_new_reminder_date == null` AND `attachment_number == 0` |
| Assessment &mdash; Awaiting Completion | 7 | `x_studio_assessment_final_reminder_date != null` |

## Behaviour

- **One email, not many.** HR receives a single digest in their inbox; nothing
  is sent to the applicants themselves.
- **Manual SMS workflow preserved.** HR copies the SMS Text column into their
  phone, texts the matching number, and then sets the SMS reminder date
  field on the applicant record so the queue clears.
- **Defensive on missing fields.** Each section field-checks at runtime, so
  the action is safe to deploy before all v5 reminder-field blocks land —
  sections whose driving field is missing are simply omitted from the
  digest (no error).
- **Does not mutate any applicant data.** No fields are stamped; no
  applicants are emailed. Pure read + render + notify-HR.
- **Blast across DB.** Even when triggered from a single applicant's form
  view, the action sweeps the whole DB. The Action-menu binding is a
  convenience entry point, not a per-record scope.

## QA on dev

1. Open dev Odoo as a recruiter once `deploy-dev` finishes.
2. Settings → Technical → Server Actions → confirm
   `BICC v5: Send SMS Queue Digest` exists, model `hr.applicant`,
   binding to the same model with view types `form,list`.
3. Recruitment → Applicants → gear icon → confirm the action shows up.
4. Click it. The bottom-of-action `log()` line reports total candidates
   and number of sections.
5. Check the HR Recruitment Manager group's inbox; one email with a
   subject like `BICC SMS Queue: N candidate(s) need a follow-up SMS`
   and one to three tables inside.
6. Click an Applicant link in the table → confirm it deep-links to the
   correct hr.applicant record.
7. On dev DBs that don't yet have v5 reminder fields, the action should
   log `queue is empty` and send nothing.

## Notes

- HTML is emitted via `mail.mail.sudo().create({body_html: ...}).send()`
  because `message_notify` / `message_post` escape HTML in SaaS safe_eval.
- The `applicant.company_id.x_studio_short_name` field is accessed via
  `hasattr` guard so the action degrades gracefully on environments
  where Studio hasn't created the multi-company short-name field.
- No `binding_view_types` value of `list` alone — both `form` and `list`
  are included so HR can fire the action from either context.
