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
   template and stamp `x_studio_resume_request_date`. Otherwise move the
   applicant straight to Stage 2 (Qualification).

**Duplicate detection is NOT done** — HR handles duplicates manually for
now.

## QA on dev

1. Pick a test job; tick **Resume Required**.
2. Create a Stage-1 applicant for that job WITHOUT attaching a resume.
3. Within ~1 minute the applicant receives the *Request for Resume* email.
4. Field **Resume Request Date** should be populated.
5. Repeat WITH attachment — applicant should auto-advance to Stage 2.
