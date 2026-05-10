# Available variables:
#  - env: environment on which the action is triggered
#  - model: model of the record on which the action is triggered; is a void recordset
#  - record: record on which the action is triggered; may be void
#  - records: recordset of all records on which the action is triggered in multi-mode; may be void
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - float_compare: utility function to compare floats based on specific precision
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - _logger: _logger.info(message): logger to emit messages in server logs
#  - UserError: exception class for raising user-facing warning messages
#  - Command: x2many commands namespace
# To return an action, assign: action = {...}


if not record.partner_id:
    if not record.partner_name:
        raise UserError(_('Please provide an applicant name.'))
    action = { record.partner_id: env['res.partner'].sudo().create({
        'is_company': False,
        'name': record.partner_name,
        'email': record.email_from,
        'phone': record.partner_phone,
        'mobile': record.partner_mobile
    })
    }

record.job_id.x_studio_emotional_assessment.check_validity()
template = env.ref('hr_recruitment_survey.mail_template_applicant_interview_invite', raise_if_not_found=False)
local_context = dict(
    default_applicant_id=record.id,
    default_partner_ids=record.partner_id.ids,
    default_survey_id=record.job_id.x_studio_emotional_assessment.id,
    default_use_template=bool(template),
    default_subject="Take Emotional Assessment Questionnaire",
    default_template_id=template and template.id or False,
    default_email_layout_xmlid='mail.mail_notification_light',
    default_deadline=datetime.datetime.now() + datetime.timedelta(hours=8)
)

action = {
    'type': 'ir.actions.act_window',
    'name': "Send an interview",
    'view_mode': 'form',
    'res_model': 'survey.invite',
    'target': 'new',
    'context': local_context,
}
