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

## Dedup scope (important)

The duplicate check is **scoped to the current applicant**, not to email
globally. The check is:

```
exists a survey.user_input with:
  email = applicant.email_from
  AND survey_id = job.x_studio_application_information
  AND create_date >= applicant.create_date
```

Anything created before this applicant's `create_date` came from a prior
application of the same person, and does NOT block a fresh dispatch.
This means a candidate who applies for a second position gets a fresh
info-survey email; their prior info-survey completion doesn't carry over.

This is intentionally different from the **assessment** dedup in
changeset 008, which keeps prior completions across applications because
assessments are once-per-candidate.

## QA on dev

1. On a test job, set Application Information Survey to a scoring survey.
2. Move a Stage-1 applicant to Stage 2 → within ~1 minute they receive the
   templated info-survey email with a unique token URL.
3. Recreate a NEW applicant record for a different job with the SAME
   email → move them to Stage 2 → they should receive a FRESH email with
   a NEW token URL (the prior application's user_input doesn't block it).
4. Action menu → Resend Info Survey → always creates a fresh token URL
   regardless of state.

## Notes

- Odoo's native `hr.recruitment.stage.template_id` is NOT set on any
  stage (verified on bicc-dev and bicc prod) so there's no overlap with
  native auto-mail. Even if a template were set there, the native flow
  can't inject a per-applicant survey token URL the way this server
  action does.
