# 010_janitor_track2

Daily 8 AM PHT cron: assessment reminders + scoring gate for Stage 7
applicants.

| Kind | xml_id |
|---|---|
| Field | `bicc_recruitment.field_hr_applicant_assessment_reminder_date` (datetime, new) |
| Template | `bicc_recruitment.tpl_score_failure` (HR uses manually) |
| Server action | `bicc_recruitment.janitor_track2` |
| Cron | `bicc_recruitment.cron_janitor_track2` (1 day, nextcall `2026-05-13 00:00:00`) |

Depends on **changeset 009** for the 3 reminder templates (general/final/non-
response). Deploy 009 first or the cron will log "Template not found" for
each Stage-7 candidate it tries to remind.

## QA on dev

Run the SA manually. Stage-7 applicants past 48h get partial-link reminders
(only the still-missing assessments). When all 3 are done: all-passed →
advance to Stage 10; any failed → kanban turns red + chatter says
"REVIEW NEEDED".
