# 009_janitor_track1

Daily 8 AM PHT cron: drain queued refusals + send cascading reminders to
Stage-1/2 applicants who haven't completed the info survey.

Ships 3 templates (General Reminder, Final Reminder, Refuse-did-not-complete)
and the SA + cron.

| Kind | xml_id |
|---|---|
| Template | `bicc_recruitment.tpl_general_reminder` |
| Template | `bicc_recruitment.tpl_final_reminder` |
| Template | `bicc_recruitment.tpl_non_response` |
| Server action | `bicc_recruitment.janitor_track1` |
| Cron | `bicc_recruitment.cron_janitor_track1` (1 day, nextcall `2026-05-13 00:00:00`) |

The 3 templates are also used by changeset 010 (Track 2) for assessment-stage
reminders.

## QA on dev

Settings → Technical → Scheduled Actions → `BICC v5: Janitor Track 1 (daily)`
→ Run Manually. Stage 1/2 applicants past the 48h threshold should get
reminders + stamped dates, or be archived if all reminders have been used.
