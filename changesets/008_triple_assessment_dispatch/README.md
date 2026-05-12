# 008_triple_assessment_dispatch

Stage-7 entry handler. Emails the 3-assessment bundle when applicant moves
to Assessment Sent. Adds a recruiter "Resend Assessment Bundle" button.

| Kind | xml_id |
|---|---|
| Template | `bicc_recruitment.tpl_triple_assessment_bundle` |
| Server action | `bicc_recruitment.triple_assessment_dispatch` |
| Automation | `bicc_recruitment.automation_triple_assessment_dispatch` (on `hr.applicant.on_write`) |
| Server action | `bicc_recruitment.resend_assessment_bundle` (binding hr.applicant Action menu, form+list) |

Depends on `hr.job.x_studio_logical_assessment` and
`hr.job.x_studio_emotional_assessment`, both already present on every env.

## QA on dev

1. Configure a test job with all 3 assessments set (Technical via the native
   survey_id, Logical + Emotional via the Studio fields).
2. Move a Stage-2 applicant to Stage 7 — they receive one bundle email with
   3 unique token URLs.
3. Try with a candidate who already completed Logical → only Technical +
   Emotional in the email; chatter logs the skip.
4. Action menu → Resend Assessment Bundle → fresh tokens for missing
   assessments only; raises a friendly UserError if all done.
