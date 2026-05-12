# 005_resume_gate

Entry-point automation. Three things on every new applicant: source detection,
duplicate check, resume gate.

| Kind | xml_id |
|---|---|
| Field | `bicc_recruitment.field_hr_applicant_resume_request_date_005` → `hr.applicant.x_studio_resume_request_date` (datetime) |
| Field | `bicc_recruitment.field_hr_job_resume_required` → `hr.job.x_studio_resume_required` (boolean) |
| Template | `bicc_recruitment.tpl_resume_request` → "Recruitment: Request for Resume (Missing Attachment)" |
| Server action | `bicc_recruitment.entry_resume_request` |
| Automation | `bicc_recruitment.automation_entry_resume_request_on_create` (fires on hr.applicant.on_create) |

## QA on dev

1. Pick a test job; tick **Resume Required**.
2. Create a Stage-1 applicant for that job WITHOUT attaching a resume.
3. Within ~1 minute the applicant receives the *Request for Resume* email.
4. Field **Resume Request Date** should be populated.
5. Repeat WITH attachment — applicant should auto-advance to Stage 2.
