# TRIGGER: hr.applicant on_write of stage_id
# MODEL: hr.applicant
# DESCRIPTION: When applicant enters Stage 7 (Assessment Sent), generate
#   per-candidate token URLs for the job's three assessments (Technical,
#   Logical, Emotional) and email a single bundle. Skips any assessment
#   already completed in a prior application (matched by email).
#
# Pure procedural — no nested defs.

STAGE_ASSESSMENT_SENT = 7
TPL_ASSESSMENT_BUNDLE = 'Recruitment: Triple Assessment Bundle'

if record.stage_id.id == STAGE_ASSESSMENT_SENT and record.email_from:
    tech_s = record.job_id.survey_id
    logi_s = record.job_id.x_studio_logical_assessment
    emot_s = record.job_id.x_studio_emotional_assessment

    # Look up surveys this candidate has already completed (any prior app)
    prior_done_inputs = env['survey.user_input'].search([
        ('email', '=', record.email_from),
        ('state', '=', 'done'),
    ])
    prior_done = prior_done_inputs.mapped('survey_id.id')

    links = []

    if tech_s:
        # Technical — always include (job-specific)
        ui = env['survey.user_input'].create({
            'survey_id': tech_s.id,
            'email': record.email_from,
            'state': 'new',
        })
        url = ui.get_start_url()
        links.append("<b>Technical Assessment:</b> <a href='%s'>%s</a>" % (url, url))

    if logi_s:
        if logi_s.id not in prior_done:
            ui = env['survey.user_input'].create({
                'survey_id': logi_s.id,
                'email': record.email_from,
                'state': 'new',
            })
            url = ui.get_start_url()
            links.append("<b>Logical Assessment:</b> <a href='%s'>%s</a>" % (url, url))
        else:
            record.message_post(body="AUTOMATION: Logical Assessment skipped (completed in previous application).")

    if emot_s:
        if emot_s.id not in prior_done:
            ui = env['survey.user_input'].create({
                'survey_id': emot_s.id,
                'email': record.email_from,
                'state': 'new',
            })
            url = ui.get_start_url()
            links.append("<b>Emotional Assessment:</b> <a href='%s'>%s</a>" % (url, url))
        else:
            record.message_post(body="AUTOMATION: Emotional Assessment skipped (completed in previous application).")

    if links:
        bundle_html = "<br/>".join(links)
        record.message_post(body="<b>ZERO-TOUCH:</b> Assessment links generated:<br/>" + bundle_html)
        tpl = env['mail.template'].search([('name', '=', TPL_ASSESSMENT_BUNDLE)], limit=1)
        if not tpl.exists():
            record.message_post(body="AUTOMATION ERROR: Template '%s' not found." % TPL_ASSESSMENT_BUNDLE)
        else:
            ctx = dict(env.context or {})
            ctx['assessment_links'] = bundle_html
            tpl.with_context(ctx).send_mail(record.id, force_send=False)
