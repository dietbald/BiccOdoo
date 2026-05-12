# TRIGGER: Daily Scheduled Action (8:00 AM PHT)
# MODEL: hr.applicant
# DESCRIPTION: Daily report listing all candidates in Stage 10 (Passed
#   Assessment) who are ready for phone interview. Shows name, phone,
#   email, position, assessment scores, days waiting, assigned recruiter.

STAGE_PASSED_ASSESSMENT = 10

now = datetime.datetime.now()
company_name = env.company.name or 'Our Company'
base_url = env['ir.config_parameter'].sudo().get_param('web.base.url', '')

hr_group = env.ref('hr_recruitment.group_hr_recruitment_manager', raise_if_not_found=False)
notify_partners = env['res.partner']
if hr_group:
    notify_partners = hr_group.user_ids.filtered('active').mapped('partner_id')

candidates = env['hr.applicant'].search(
    [('active', '=', True), ('stage_id', '=', STAGE_PASSED_ASSESSMENT)],
    order='date_last_stage_update desc',
)

if candidates and notify_partners:
    rows = ""
    for rec in candidates:
        name = rec.partner_name or 'Unknown'
        phone = rec.partner_phone_sanitized or rec.partner_phone or 'N/A'
        email = rec.email_from or 'N/A'
        position = rec.job_id.name if rec.job_id else 'N/A'
        recruiter = rec.user_id.name if rec.user_id else 'Unassigned'

        date_reached = ''
        if rec.date_last_stage_update:
            date_reached = rec.date_last_stage_update.strftime('%b %d, %Y')
        elif rec.write_date:
            date_reached = rec.write_date.strftime('%b %d, %Y')

        if rec.date_last_stage_update:
            days_waiting = (now - rec.date_last_stage_update).days
        else:
            days_waiting = 0

        # Build survey_ids list inline (no comp closures)
        job = rec.job_id
        survey_ids = []
        if job:
            if job.survey_id:
                survey_ids.append(job.survey_id.id)
            if job.x_studio_logical_assessment:
                survey_ids.append(job.x_studio_logical_assessment.id)
            if job.x_studio_emotional_assessment:
                survey_ids.append(job.x_studio_emotional_assessment.id)

        score_parts = []
        if survey_ids:
            completed = env['survey.user_input'].search([
                ('email', '=', rec.email_from),
                ('state', '=', 'done'),
                ('survey_id', 'in', survey_ids),
            ])
            for inp in completed:
                if inp.survey_id.scoring_type == 'no_scoring':
                    pct = 'N/A'
                    passed = '-'
                else:
                    pct = "%.0f%%" % (inp.scoring_percentage or 0)
                    passed = 'PASS' if inp.scoring_success else 'FAIL'
                score_parts.append("%s: %s (%s)" % (inp.survey_id.title or 'Survey', pct, passed))

        scores_text = "<br/>".join(score_parts) if score_parts else 'No scored assessments'

        wait_style = ""
        if days_waiting > 2:
            wait_style = " style='color:red;font-weight:bold;'"
        elif days_waiting > 1:
            wait_style = " style='color:orange;'"

        link = "%s/odoo/recruitment-applications/%s" % (base_url, rec.id)

        rows += "<tr>"
        rows += "<td><a href='%s'>%s</a></td>" % (link, name)
        rows += "<td><a href='tel:%s'>%s</a></td>" % (phone, phone)
        rows += "<td>%s</td>" % email
        rows += "<td>%s</td>" % position
        rows += "<td>%s</td>" % scores_text
        rows += "<td>%s</td>" % date_reached
        rows += "<td%s>%d day(s)</td>" % (wait_style, days_waiting)
        rows += "<td>%s</td>" % recruiter
        rows += "</tr>"

    body_html = (
        "<h2>Phone Interview Queue - Daily Report</h2>"
        "<p>As of %s - <b>%d candidate(s)</b> ready for phone interview.</p>"
        "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;font-size:13px;'>"
        "<thead><tr style='background-color:#f0f0f0;'>"
        "<th>Candidate</th><th>Phone</th><th>Email</th><th>Position</th>"
        "<th>Assessment Scores</th><th>Date Reached</th><th>Waiting</th><th>Recruiter</th>"
        "</tr></thead><tbody>%s</tbody></table>"
        "<br/><p style='font-size:12px;color:#666;'>Candidates waiting more than 2 days are highlighted. "
        "Please schedule phone interviews promptly to avoid losing top talent.</p>"
    ) % (now.strftime('%B %d, %Y'), len(candidates), rows)

    recipient_cmds = []
    for pid in notify_partners.ids:
        recipient_cmds.append((4, pid))

    env['mail.mail'].sudo().create({
        'subject': "Phone Interview Queue - %s (%d candidates)" % (now.strftime('%b %d'), len(candidates)),
        'body_html': body_html,
        'recipient_ids': recipient_cmds,
        'auto_delete': True,
    }).send()
    log("Phone interview report: %d candidate(s) → %d recipient(s)" % (len(candidates), len(notify_partners)))
else:
    log("Phone interview report: candidates=%d recipients=%d — nothing to send" % (len(candidates), len(notify_partners)))
