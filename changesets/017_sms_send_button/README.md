# 017_sms_send_button

Per-applicant manual SMS popup. Replaces the "edit the date field by hand"
step after HR sends an SMS.

| Kind | xml_id |
|---|---|
| Field | `bicc_recruitment.field_hr_applicant_sms_preview` → `hr.applicant.x_studio_sms_preview` (Text) |
| Server action | `bicc_recruitment.mark_sms_sent` (called by the popup's "SMS Sent" button) |
| View | `bicc_recruitment.sms_wizard_form_view` (the popup form arch) |
| Server action | `bicc_recruitment.send_sms_button` (entry point, bound to hr.applicant Action menu form+list) |

## Workflow

1. HR opens an applicant and clicks **gear icon → Send SMS Reminder**.
2. The button SA figures out which queue the applicant is in (from
   `stage_id` + `attachment_number`), builds the matching SMS text,
   writes it to `x_studio_sms_preview`, and opens the popup.
3. The popup shows the applicant's name, mobile, and the SMS text —
   all read-only and selectable for copy.
4. HR triple-clicks the phone or the message body to select, copies,
   and sends from their phone.
5. HR clicks **SMS Sent** → matching date field stamped, preview field
   cleared, chatter line posted, popup closes. The applicant drops off
   the next SMS Queue Digest run.
6. **Cancel** closes without any state change.

## Stage routing

| Stage | SMS wording | Field stamped |
|---|---|---|
| 1 (New) + no attachment | resume-missing | `x_studio_sms_new_reminder_date` |
| 2 (Qualification) | info-survey | `x_studio_sms_reminder_date` |
| 7 (Assessment Sent) | assessment | `x_studio_assessment_sms_reminder_date` |
| anything else | UserError "no SMS template for stage X" | — |

The three SMS texts are the same ones the digest in changeset 002 puts
in its 3-column table.

## QA on dev

1. Open an applicant in Stage 1 (New) with **no attachments** → gear
   icon → Send SMS Reminder → popup shows the resume-missing message
   with `Hi {first_name}, BICC HR here. We got your application…`.
   Click SMS Sent → applicant form refreshes with the date stamped.
2. Repeat on a Stage 2 applicant → gets the info-survey wording.
3. Repeat on a Stage 7 applicant → gets the assessment wording.
4. Try on a Stage 5 (Offer Proposal) applicant → UserError popup
   listing the supported stages.
5. Click Cancel on the popup → no change to any field, applicant
   record untouched.

## Notes

- `x_studio_sms_preview` is just a scratch Text field. The "SMS Sent"
  path clears it after stamping. The Cancel path leaves it populated
  until the next Send-SMS click overwrites it — minor clutter, no
  data leak.
- `send_sms_button` is closure-free (matches safe_eval rules), as is
  `mark_sms_sent`.
- The view's `<footer>` overrides Odoo's default modal footer, so
  HR sees only the two buttons we define.
