# 002_sms_followup_email_blast

## What changes

Adds a manual server action **"BICC v5: Send SMS Follow-up Email Blast"** to
the hr.applicant Action menu (visible in form and list views). When triggered,
it emails every applicant currently in the SMS follow-up queue — the same
three populations that the daily SMS digest cron surfaces for HR to SMS by
hand:

| Section | Stage | Queue criterion |
|---|---|---|
| Qualification | 2 (Qualification) | `x_studio_reminder_date != null` AND `x_studio_sms_reminder_date == null` |
| Resume missing | 1 (New) | `x_studio_resume_request_date != null` AND `x_studio_sms_new_reminder_date == null` AND no attachments |
| Assessment | 7 (Assessment Sent) | `x_studio_assessment_final_reminder_date != null` |

Email subject and body mirror the SMS wording HR provided. First name, company
short name (`x_studio_short_name`, e.g. BICC or IGEBC), and job title are
substituted per applicant. No "Last Name – No Email" format text — applicants
just reply naturally.

## Behaviour

- **Blast, not per-record.** Even when HR triggers the action from a single
  applicant's form view, the action sweeps all three queue populations across
  the whole DB. Each applicant's own chatter records `MANUAL ACTION: Follow-up
  email sent (qual|resume|assessment queue).`
- **Defensive on missing fields.** Each section introspects whether its
  driving custom field exists before searching. Sections whose field isn't
  present yet (because the corresponding v5 block hasn't been deployed to
  this Odoo instance) are skipped silently — the action will simply email
  fewer people, never crash.
- **Does not stamp `x_studio_sms_*_date`.** SMS remains a separate channel
  HR may still send manually after this blast.
- **No applicant gets a duplicate.** Within a single run, populations are
  filtered to be disjoint by stage. Re-running the action a second time can
  re-send to the same applicants — by design, since HR may want to follow up
  again after a few days.

## QA on dev

1. Once `deploy-dev` lands, open dev Odoo as a recruiter.
2. Settings → Technical → Server Actions → find `BICC v5: Send SMS Follow-up
   Email Blast`. Confirm `binding_model = hr.applicant` and the gear-menu
   binding shows up on Recruitment → Applicants.
3. Trigger from the gear menu of any applicant. The log line at the bottom
   of the action reports `qual=N resume=N assessment=N (total=N)`.
4. Spot-check three applicants' chatter for the `MANUAL ACTION: Follow-up
   email sent (... queue)` line.
5. Inspect outgoing mail (Settings → Technical → Email → Emails) and confirm
   the subject and body wording matches: first name greeting, no em-dashes,
   no "Last Name – No Email" format text.
6. On dev DBs that don't yet have v5 reminder fields, the action should
   simply log `qual=0 resume=0 assessment=0` and write no chatter / emails.

## Notes

- Uses `mail.mail.sudo().create({body_html: ...}).send()` per the SaaS
  safe_eval HTML rule — message_post and message_notify escape HTML.
- `applicant.company_id.x_studio_short_name` is accessed via `hasattr` guard
  so the action degrades gracefully on environments where Studio hasn't
  created the field (falls back to `company_id.name`).
- No rollback gotchas — this changeset only creates one server action. CI
  auto-rollback on failure cleanly removes it.
