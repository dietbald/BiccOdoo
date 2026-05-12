# 005_resume_gate

Entry-point automation on `hr.applicant.on_create`. Two things on every new
applicant: source detection and a scoped resume gate.

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
   keywords (`via SEEK`, `via JobStreet`, `via Indeed`, `via LinkedIn`,
   `via Facebook`, `OnlineJobs.ph`) and sets `source_id` to the matching
   `utm.source`. Cleans the "via XXXX" suffix from the applicant's name.
   The OnlineJobs case posts a chatter warning because the forwarded
   notification usually has the wrong name.

2. **Resume gate (scoped).** If the job has `x_studio_resume_required =
   True` AND the applicant has zero attachments, the script decides
   whether to email the *Request for Resume* template. **Auto-trigger
   channels** (email fires):

   - source detected as **Facebook**
   - source detected as **Jobstreet** (via SEEK or via JobStreet)
   - applicant created by the **public/portal user** with no detected
     source — i.e. the website careers form

   **Not auto-triggered** (chatter logs the skip; HR handles manually):

   - Indeed (source = "Search engine")
   - LinkedIn (source = "LinkedIn")
   - OnlineJobs (source = "OnlineJobs")
   - HR users creating manually
   - Anything else with no matching source

## What it does NOT do

- **No `stage_id` writes.** Whether the applicant moves to Stage 2 is
  entirely n8n's call (n8n's local poll watches for attachments and moves
  applicants when ready). HR can also do it manually.
- **No duplicate detection.** HR handles dups manually for now.

## QA on dev

1. Pick a test job; tick **Resume Required**.
2. Create an applicant with `partner_name = "Maria Cruz via Indeed"`, no
   resume → applicant lands in Stage 1, source set to `Search engine`,
   chatter logs *"Auto-request email skipped - channel 'Search engine'
   is not in the auto-trigger list"*. No email goes out.
3. Repeat with `partner_name = "Juan Dela Cruz via Facebook"` → applicant
   lands in Stage 1, source = `Facebook`, chatter logs *"Request sent
   (channel: Facebook)"*. Email goes out.
4. Submit a public-form applicant via the website careers page with no
   resume → applicant lands in Stage 1 with no source, chatter logs
   *"Request sent (channel: website form)"*. Email goes out.
5. As an HR user, manually create an applicant with no resume → applicant
   lands in Stage 1, chatter logs *"Auto-request email skipped - channel
   'manual / unknown' is not in the auto-trigger list"*. No email.

## Notes

- "Public user" detection uses `env.ref('base.public_user')`; this is
  Odoo's standard public/portal user for unauthenticated form
  submissions.
- The trigger list is a constant at the top of the script
  (`EMAIL_TRIGGER_SOURCES`). Edit it if HR's channel mix changes.
- This action never moves applicants — n8n owns the Stage 1 → Stage 2
  transition based on attachment uploads.
