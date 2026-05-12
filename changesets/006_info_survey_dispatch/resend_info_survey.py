# TRIGGER: Manual button on hr.applicant (Action menu, form + list)
# MODEL: hr.applicant
# DESCRIPTION: Recruiter button to (re)send the Information Confirmation
#   survey link to a candidate. Creates a fresh user_input token each
#   time so the link is always valid.

TPL_INFO_SURVEY = 'Recruitment: Information Confirmation Survey'

if not record.job_id:
    raise UserError("Cannot resend: applicant has no job position.")
if not record.email_from:
    raise UserError("Cannot resend: applicant has no email on file.")

survey = record.job_id.x_studio_application_information
if not survey:
    raise UserError("Job Position '%s' has no Application Information survey set." % record.job_id.name)

user_input = env['survey.user_input'].create({
    'survey_id': survey.id,
    'email': record.email_from,
    'state': 'new',
})

tpl = env['mail.template'].search([('name', '=', TPL_INFO_SURVEY)], limit=1)
if not tpl.exists():
    raise UserError("Could not find template '%s'." % TPL_INFO_SURVEY)

ctx = dict(env.context or {})
ctx['survey_link'] = user_input.get_start_url()

tpl.with_context(ctx).send_mail(record.id, force_send=False)
record.message_post(body="MANUAL ACTION: Resent Information Confirmation survey link.")
