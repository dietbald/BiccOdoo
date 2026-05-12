# TRIGGER: Manual button on hr.applicant (Action menu, form + list)
# MODEL: hr.applicant
# DESCRIPTION: Recruiter button to (re)send the assessment bundle. Builds
#   fresh user_input tokens but only for assessments the candidate hasn't
#   completed yet. If all are done, raises a friendly user error.

TPL_ASSESSMENT_BUNDLE = 'Recruitment: Triple Assessment Bundle'

if not record.job_id:
    raise UserError("Cannot resend: applicant has no job position.")
if not record.email_from:
    raise UserError("Cannot resend: applicant has no email on file.")

tech_s = record.job_id.survey_id
logi_s = record.job_id.x_studio_logical_assessment
emot_s = record.job_id.x_studio_emotional_assessment

prior_done_inputs = env['survey.user_input'].search([
    ('email', '=', record.email_from),
    ('state', '=', 'done'),
])
prior_done = prior_done_inputs.mapped('survey_id.id')

links = []

if tech_s and tech_s.id not in prior_done:
    ui = env['survey.user_input'].create({'survey_id': tech_s.id, 'email': record.email_from, 'state': 'new'})
    url = ui.get_start_url()
    links.append("<b>Technical Assessment:</b> <a href='%s'>%s</a>" % (url, url))

if logi_s and logi_s.id not in prior_done:
    ui = env['survey.user_input'].create({'survey_id': logi_s.id, 'email': record.email_from, 'state': 'new'})
    url = ui.get_start_url()
    links.append("<b>Logical Assessment:</b> <a href='%s'>%s</a>" % (url, url))

if emot_s and emot_s.id not in prior_done:
    ui = env['survey.user_input'].create({'survey_id': emot_s.id, 'email': record.email_from, 'state': 'new'})
    url = ui.get_start_url()
    links.append("<b>Emotional Assessment:</b> <a href='%s'>%s</a>" % (url, url))

if not links:
    raise UserError("Candidate has already completed all required assessments for this role.")

bundle_html = "<br/>".join(links)
tpl = env['mail.template'].search([('name', '=', TPL_ASSESSMENT_BUNDLE)], limit=1)
if not tpl.exists():
    raise UserError("Could not find template '%s'." % TPL_ASSESSMENT_BUNDLE)

ctx = dict(env.context or {})
ctx['assessment_links'] = bundle_html
tpl.with_context(ctx).send_mail(record.id, force_send=False)
record.message_post(body="MANUAL ACTION: Resent Assessment Bundle links (missing surveys only).")
