# 005_resume_gate

Entry-point automation on `hr.applicant.on_create`. Two things on every new
applicant: source detection and the resume gate.

| Kind | xml_id |
|---|---|
| Template | `bicc_recruitment.tpl_resume_request` → "Recruitment: Request for Resume (Missing Attachment)" |
| Server action | `bicc_recruitment.entry_resume_request` |
| Automation | `bicc_recruitment.automation_entry_resume_request_on_create` (fires on `hr.applicant.on_create`) |

The two fields the gate reads (`hr.applicant.x_studio_resume_request_date`
and `hr.job.x_studio_resume_required`) already exist on every target env via
Studio on prod / prior-push on dev / prod-clone on staging — this changeset
does not re-declare them.

## What it does

1. **Source auto-detection.** Scans `partner_name` + `email_from` for
   keywords (Indeed / LinkedIn / Facebook / Jobstreet / OnlineJobs) and
   sets `source_id` to the matching `utm.source`. Cleans the "via XXXX"
   suffix from the applicant's name.
2. **Resume gate.** If the job's `x_studio_resume_required` is true and
   the applicant has zero attachments, email the *Request for Resume*
   template and stamp `x_studio_resume_request_date` — **but only when
   `create_uid` is NOT an HR Recruitment user**. HR manual creates skip
   the email so HR can attach the resume seconds later without spamming
   the candidate. External creates (website form, n8n webhook, API
   uploads) DO get the email immediately, because their create_uid is a
   public / bot / API user with no HR group. Otherwise (resume present,
   or job doesn't require one) move the applicant straight to Stage 2
   (Qualification).

**Duplicate detection is NOT done** — HR handles duplicates manually for
now.

## QA on dev

1. Pick a test job; tick **Resume Required**.
2. As an HR user, create a Stage-1 applicant for that job WITHOUT a
   resume → applicant lands in Stage 1, no email goes out, chatter logs
   *"AUTOMATION: Created by HR user (…). Resume-request email skipped"*.
3. Attach a resume manually. (n8n's poll will move them to Stage 2; or
   move them yourself.)
4. Submit a public-form applicant for the same job (or post via API) with
   no resume → applicant gets the *Request for Resume* email and
   `x_studio_resume_request_date` is stamped.
5. Submit with a resume attached → applicant auto-advances to Stage 2.

## Notes

- The HR-user check uses `record.create_uid.has_group('hr_recruitment.group_hr_recruitment_user')`.
  Manager implies User implies Interviewer in Odoo's hr_recruitment group
  hierarchy, so any HR user above the basic Interviewer level will skip
  the email. If you want a tighter or looser scope, change the group ref.
- Edge case: a non-HR internal user (e.g. a department head with only
  Interviewer rights) creating an applicant manually WILL still trigger
  the email. Acceptable for v1.
- If n8n's API user is given HR-recruitment-user rights, the email path
  will be silently skipped for n8n-created applicants. Make sure n8n's
  API user is a portal/integration user with no HR groups.
