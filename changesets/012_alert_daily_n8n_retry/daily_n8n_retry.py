# TRIGGER: Scheduled Action (Daily, 2:00 AM PHT)
# MODEL: hr.applicant
# DESCRIPTION: Identify applicants stuck in Stage 1 (New) for > 24h and
#   alert the HR Recruitment Manager group. n8n picks these up via its
#   scheduled JSON-RPC poll (Odoo SaaS forbids outbound HTTP).

STAGE_NEW = 1

now = datetime.datetime.now()
company_name = env.company.name or 'Our Company'
base_url = env['ir.config_parameter'].sudo().get_param('web.base.url', '')

hr_group = env.ref('hr_recruitment.group_hr_recruitment_manager', raise_if_not_found=False)
notify_partners = env['res.partner']
if hr_group:
    notify_partners = hr_group.user_ids.filtered('active').mapped('partner_id')

stuck_applicants = env['hr.applicant'].search([
    ('stage_id', '=', STAGE_NEW),
    ('create_date', '<', (now - datetime.timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')),
])

if stuck_applicants and notify_partners:
    summary_html = ""
    for applicant in stuck_applicants:
        days_stuck = (now - applicant.create_date).days
        link = "%s/odoo/recruitment-applications/%s" % (base_url, applicant.id)
        summary_html += (
            "<li><a href='%s'><b>%s</b></a> - %s (stuck %s day(s))</li>"
        ) % (link, applicant.partner_name or 'Unknown', applicant.job_id.name or 'No Job', days_stuck)
        applicant.message_post(body="AUTOMATION: Flagged as stuck in New stage for >24h. Awaiting n8n re-processing.")

    body_html = (
        "<h3>Daily n8n Retry Report</h3>"
        "<p>The following %d applicant(s) have been in the 'New' stage for over 24 hours "
        "and may need n8n re-processing.</p>"
        "<ul>%s</ul>"
        "<p>n8n should pick these up automatically via its scheduled poll. "
        "If they remain stuck, check the n8n workflow and Odoo webhook configuration.</p>"
    ) % (len(stuck_applicants), summary_html)
    subject = "%s Automation: %d applicant(s) stuck in New stage" % (company_name, len(stuck_applicants))

    recipient_cmds = []
    for pid in notify_partners.ids:
        recipient_cmds.append((4, pid))

    env['mail.mail'].sudo().create({
        'subject': subject,
        'body_html': body_html,
        'recipient_ids': recipient_cmds,
        'auto_delete': True,
    }).send()
    log("Daily n8n retry: %d stuck / %d recipients" % (len(stuck_applicants), len(notify_partners)))
else:
    log("Daily n8n retry: stuck=%d recipients=%d — nothing to send" % (len(stuck_applicants), len(notify_partners)))
