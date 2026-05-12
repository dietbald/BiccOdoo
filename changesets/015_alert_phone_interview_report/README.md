# 015_alert_phone_interview_report

Daily 8 AM PHT cron. Phone-interview queue for HR.

| Kind | xml_id |
|---|---|
| Server action | `bicc_recruitment.phone_interview_report` |
| Cron | `bicc_recruitment.cron_phone_interview_report` — every 1 day, nextcall `2026-05-13 00:00:00` |

Lists Stage-10 applicants with name + phone (`tel:` link) + email + job +
assessment scores + days waiting (color-coded). Red ≥ 3 days, orange ≥ 2.
