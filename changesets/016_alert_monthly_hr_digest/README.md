# 016_alert_monthly_hr_digest

Weekly Mon 8 AM PHT cron with internal "last Monday of month" gate. Sends one
per-company HR digest (model `hr.employee`) covering next-month: birthdays,
anniversary milestones, expiring contracts, public holidays, headcount.

| Kind | xml_id |
|---|---|
| Server action | `bicc_recruitment.monthly_hr_digest` (model `hr.employee`) |
| Cron | `bicc_recruitment.cron_monthly_hr_digest` — every 1 week, nextcall `2026-05-18 00:00:00` |

## QA on dev

Settings → Technical → Server Actions → `BICC v5: Monthly HR Digest` → **Run Manually** (bypasses the last-Monday gate). HR Manager group inbox gets one digest per company that has employees.
