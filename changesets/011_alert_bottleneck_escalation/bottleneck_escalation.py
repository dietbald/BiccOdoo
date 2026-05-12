# TRIGGER: Scheduled Action (Daily, 8 AM PHT)
# MODEL: hr.applicant
# DESCRIPTION: Daily bottleneck alert. Lists applicants stuck in Stage 10
#   (Passed Assessment) for >48h and emails the HR Recruitment Manager
#   group so they advance/refuse manually. Pure procedural — no closures.

STAGE_PASSED_ASSESSMENT = 10

now = datetime.datetime.now()
company_name = env.company.name or 'Our Company'
base_url = env['ir.config_parameter'].sudo().get_param('web.base.url', '')

hr_group = env.ref('hr_recruitment.group_hr_recruitment_manager', raise_if_not_found=False)
notify_partners = env['res.partner']
if hr_group:
    notify_partners = hr_group.user_ids.filtered('active').mapped('partner_id')

stagnant_candidates = env['hr.applicant'].search([
    ('active', '=', True),
    ('stage_id', '=', STAGE_PASSED_ASSESSMENT),
    ('write_date', '<', (now - datetime.timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')),
])

if stagnant_candidates and notify_partners:
    summary_html = ""
    for c in stagnant_candidates:
        days_stuck = (now - c.write_date).days
        link = "%s/odoo/recruitment-applications/%s" % (base_url, c.id)
        summary_html += (
            "<li><a href='%s'><b>%s</b></a> - %s (stuck %s day(s))</li>"
        ) % (link, c.partner_name or 'Unknown', c.job_id.name or 'N/A', days_stuck)

    subject = "%s Recruitment Bottleneck: %d candidate(s) need review" % (
        company_name, len(stagnant_candidates))
    body_html = (
        "<h3>Bottleneck Alert</h3>"
        "<p>The candidates below have passed assessments but haven't moved "
        "to the next stage in over 48 hours.</p>"
        "<ul>%s</ul>"
        "<p>Please review and advance or refuse them in the Odoo recruitment pipeline.</p>"
    ) % summary_html

    recipient_cmds = []
    for pid in notify_partners.ids:
        recipient_cmds.append((4, pid))

    env['mail.mail'].sudo().create({
        'subject': subject,
        'body_html': body_html,
        'recipient_ids': recipient_cmds,
        'auto_delete': True,
    }).send()
    log("Bottleneck escalation: %d stagnant candidate(s) escalated to %d HR partner(s)." % (
        len(stagnant_candidates), len(notify_partners)))
else:
    log("Bottleneck escalation: %d stagnant / %d HR partners — nothing to send." % (
        len(stagnant_candidates), len(notify_partners)))
