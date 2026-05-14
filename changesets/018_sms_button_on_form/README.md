# 018_sms_button_on_form

Adds a header button **SMS** on the hr.applicant form, next to the existing
Studio-added Req Info / n8n / Remind buttons. Visible only when the
applicant is in an SMS-eligible state.

| Kind | xml_id |
|---|---|
| Inherited view | `bicc_recruitment.applicant_form_sms_button_inherit` (inherits `hr_recruitment.hr_applicant_view_form`) |

## When the button shows

| Stage | Additional conditions to be visible |
|---|---|
| 1 (New) | `attachment_number == 0` AND `x_studio_sms_new_reminder_date` is null |
| 2 (Qualification) | `x_studio_sms_reminder_date` is null |
| 7 (Assessment Sent) | `x_studio_assessment_sms_reminder_date` is null |
| Anything else | hidden |

So the button disappears the moment HR clicks it and the matching SMS date
gets stamped, or when the applicant moves out of an SMS-eligible stage.

## What the button does

Calls the server action `bicc_recruitment.send_sms_button` (created in
changeset 017). That fires the same SMS preview modal you'd get from the
gear-icon "Send SMS Reminder" entry, with Cancel / SMS Sent buttons in
the footer.

## QA on dev

1. Open a Stage-1 applicant with no resume — the **SMS** button should
   appear in the form header alongside Req Info / n8n / Remind.
2. Click it — the SMS preview popup opens with the resume-missing
   message.
3. Click SMS Sent in the popup → applicant form refreshes, the SMS
   button vanishes (because `x_studio_sms_new_reminder_date` is now
   stamped).
4. Move the applicant to a non-SMS stage (e.g. Stage 5 Offer Proposal) —
   button is hidden.

## Notes

- Inheriting from `hr_recruitment.hr_applicant_view_form` (id 1686).
  Studio's existing customization (view 4835) inherits from the same
  parent, so all four buttons (Req Info, n8n, Remind, SMS) end up
  side-by-side; exact ordering depends on view priority.
- The four invisible `<field>` declarations inside `<sheet>` exist so
  the button's `invisible="…"` expression can evaluate against those
  values. Without them, the form record wouldn't load those fields and
  the expression would always evaluate as if the dates are null.
