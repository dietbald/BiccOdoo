# 006_info_survey_dispatch

Stage-2 entry handler. Emails the Application Information Confirmation
survey link to applicants moving into Qualification. Adds a recruiter
"Resend Info Survey" button to the hr.applicant Action menu.

| Kind | xml_id |
|---|---|
| Template | `bicc_recruitment.tpl_info_survey` — `Recruitment: Information Confirmation Survey` |
| Server action | `bicc_recruitment.info_survey_dispatch` |
| Automation | `bicc_recruitment.automation_info_survey_dispatch` (on `hr.applicant.on_write`) |
| Server action | `bicc_recruitment.resend_info_survey` (binding hr.applicant Action menu, form+list) |

Depends on `hr.job.x_studio_application_information` (m2o → survey.survey),
which already exists on every target env.

## QA on dev

1. On a test job, set Application Information Survey to a scoring survey.
2. Move a Stage-1 applicant to Stage 2 → within ~1 minute they receive the
   templated info-survey email with a unique token URL.
3. Action menu → Resend Info Survey → fresh token URL is created and sent.
