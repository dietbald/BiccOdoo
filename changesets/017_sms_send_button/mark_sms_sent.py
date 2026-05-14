# TRIGGER: Called by the "SMS Sent" button in the SMS popup form view.
# MODEL: hr.applicant
# DESCRIPTION: Stamp the right x_studio_sms_*_date field based on the
#   applicant's current stage, clear both the preview and the
#   phone-warning fields, post a chatter audit line, and close the
#   modal dialog.
#
# Pure procedural — no closures.

STAGE_NEW = 1
STAGE_QUALIFICATION = 2
STAGE_ASSESSMENT_SENT = 7

stage = record.stage_id.id
field_to_stamp = None
queue = None
if stage == STAGE_QUALIFICATION:
    field_to_stamp = 'x_studio_sms_reminder_date'
    queue = 'qualification'
elif stage == STAGE_NEW and record.attachment_number == 0:
    field_to_stamp = 'x_studio_sms_new_reminder_date'
    queue = 'resume'
elif stage == STAGE_ASSESSMENT_SENT:
    field_to_stamp = 'x_studio_assessment_sms_reminder_date'
    queue = 'assessment'

if not field_to_stamp:
    raise UserError("Cannot mark SMS sent — applicant is in an unsupported stage.")

record.write({
    field_to_stamp: datetime.datetime.now(),
    'x_studio_sms_preview': False,
    'x_studio_sms_phone_display': False,
})
record.message_post(body=(
    "MANUAL SMS: Marked as sent (%s queue, field %s)."
) % (queue, field_to_stamp))

action = {'type': 'ir.actions.act_window_close'}
