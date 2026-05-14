# TRIGGER: Manual button on hr.applicant (Action menu, form + list)
# MODEL: hr.applicant
# DESCRIPTION: Entry point for "Send SMS Reminder". Builds the SMS text
#   appropriate for the applicant's current stage, stashes it in
#   x_studio_sms_preview, and opens a modal popup form view with two
#   buttons: Cancel (closes, no state change) and SMS Sent (calls the
#   bicc_recruitment.mark_sms_sent action which stamps the right
#   x_studio_sms_*_date).
#
#   No state change here other than the preview-field stash. The
#   *_date fields are stamped only when HR clicks SMS Sent.
#
# Pure procedural — no closures.

STAGE_NEW = 1
STAGE_QUALIFICATION = 2
STAGE_ASSESSMENT_SENT = 7

# Detect whether res.company has x_studio_short_name (multi-company branding).
# hasattr is NOT in the Odoo SaaS safe_eval allowlist — check via ir.model.fields.
has_short_name = bool(env['ir.model.fields'].sudo().search(
    [('model', '=', 'res.company'), ('name', '=', 'x_studio_short_name')], limit=1))

co_short = False
if record.company_id and has_short_name:
    co_short = record.company_id.x_studio_short_name
co = co_short or (record.company_id.name if record.company_id else 'BICC')
first_name = (record.partner_name or 'there').split(' ')[0]
job = record.job_id.name if record.job_id else 'open'

sms_text = None
if record.stage_id.id == STAGE_QUALIFICATION:
    sms_text = (
        "Hi %s, this is %s HR. We sent you the Applicant Information form "
        "for the %s role a few days back. Could you fill it out so we can "
        "keep things moving? If you didn't get our email, let us know."
    ) % (first_name, co, job)
elif record.stage_id.id == STAGE_NEW and record.attachment_number == 0:
    sms_text = (
        "Hi %s, %s HR here. We got your application for the %s role but "
        "didn't see a resume attached. Could you reply to our email with it? "
        "If you never got our email, let us know."
    ) % (first_name, co, job)
elif record.stage_id.id == STAGE_ASSESSMENT_SENT:
    sms_text = (
        "Hi %s, %s HR here. Have you had a chance to do the assessment we "
        "emailed you for the %s role? Please send it back when you can. "
        "If you can't find our email, let us know."
    ) % (first_name, co, job)

if not sms_text:
    raise UserError(
        "Applicant '%s' is in stage '%s' which has no SMS reminder template.\n\n"
        "SMS reminders apply only to:\n"
        "  - Stage 1 (New) with no resume attached\n"
        "  - Stage 2 (Qualification)\n"
        "  - Stage 7 (Assessment Sent)"
        % (record.partner_name or 'Unknown', record.stage_id.name or 'unknown')
    )

# Stash the SMS preview text on the applicant so the popup view can show it
record.write({'x_studio_sms_preview': sms_text})

# Open the popup form view as a modal dialog
view = env.ref('bicc_recruitment.sms_wizard_form_view', raise_if_not_found=False)
action = {
    'type': 'ir.actions.act_window',
    'name': 'Send SMS Reminder',
    'res_model': 'hr.applicant',
    'res_id': record.id,
    'view_mode': 'form',
    'view_id': view.id if view else False,
    'target': 'new',
}
