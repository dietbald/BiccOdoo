# 004_star_talent_alert

## What changes

Whenever a `survey.user_input` is marked done with `scoring_percentage ≥ 90`,
and the email matches an hr.applicant, this:

- Sets `priority='3'` (★★★ in the kanban view)
- Posts a chatter alert tagging the assigned recruiter (`user_id.partner_id`)
  so they get an inbox notification
- Logs a "MANAGEMENT" trail line

Pure routing. No fields, no templates.

## What gets deployed

| Kind | Name |
|---|---|
| server action | `bicc_recruitment.star_talent_alert` |
| automation | `bicc_recruitment.automation_star_talent_alert` on `survey.user_input.on_write` |

## QA on dev

1. Submit a scoring survey via its public token URL with answers totalling ≥ 90%.
2. Within ~1 second the matching applicant's priority should turn gold-star
   (3 stars) and chatter shows *"STAR CANDIDATE ALERT: … Call them immediately!"*.
3. The assigned recruiter (`user_id`) gets an inbox notification.

## Notes

- Fires on ANY survey, not just the technical assessment — high info-survey
  scores also flag star talent.
- Match is `email_from == record.email`, most recent by `id desc` for
  duplicates.
- Coexists with Block 04 (info survey adjudication) — both fire on the
  same trigger, independently.
