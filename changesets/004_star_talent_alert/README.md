# 004_star_talent_alert

## What changes

Flags an applicant as Star Talent **only when both the Logical and Technical
assessments are done and meet the dual threshold**:

| Survey | Threshold |
|---|---|
| `hr.job.x_studio_logical_assessment` (Logical) | ≥ 90% |
| `hr.job.survey_id` (Technical, native) | ≥ 80% |

When the gate passes:
- `applicant.priority = '3'` (★★★ in kanban)
- Chatter alert tagging the assigned recruiter (`user_id.partner_id`) →
  recruiter gets an inbox notification
- "MANAGEMENT" trail line for audit

The trigger is `survey.user_input.on_write`, but the script early-exits if
the submitted survey isn't the Technical or Logical for the applicant's
job. So submitting the Emotional / Info survey does not re-fire the alert.

Dedup: if `applicant.priority == '3'` already, the alert is skipped to
avoid spamming the recruiter on assessment retakes.

## What gets deployed

| Kind | Name |
|---|---|
| server action | `bicc_recruitment.star_talent_alert` |
| automation | `bicc_recruitment.automation_star_talent_alert` on `survey.user_input.on_write` |

## QA on dev

1. Pick a test applicant for a job that has both a Logical and a Technical
   assessment configured (`hr.job.x_studio_logical_assessment` set + the
   native `survey_id`).
2. Submit just one of the two with ≥ 90% / ≥ 80% — no alert (the other
   side isn't done yet).
3. Submit the second one with a passing score — within ~1 sec, applicant
   priority should turn ★★★ and chatter shows
   *"STAR CANDIDATE ALERT: … scored Logical X% + Technical Y% for …"*.
4. Re-submit either assessment (retake) — no second alert (priority is
   already 3).
5. Submit a result that drops below either threshold (e.g. Logical 85% +
   Technical 90%) — no alert.

## Notes

- Coexists with `007_info_survey_adjudication` which also fires on
  `survey.user_input.on_write` and uses its own ≥ 90% info-survey rule
  to set priority. Both automations run independently; if 007 already
  bumped the priority to ★★★ from a high info-survey score, 004 will
  detect that and skip its alert (priority dedup).
- Match between user_input and applicant is `record.email ==
  email_from`, most recent by `id desc` for duplicate emails.
- Chatter body is plain text — `message_post` in SaaS safe_eval HTML-
  escapes its body, so HTML formatting wouldn't render anyway.
