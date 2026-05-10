# TRIGGER: Daily Scheduled Action (9:00 AM PHT)
# MODEL: hr.applicant
# DESCRIPTION: v5.0 Combined SMS action queue — Section 1: Qualification stage (info survey pending),
#   Section 2: Resume missing (Stage 1). Uses group-based notification.

# ── Stage Constants ──
STAGE_NEW = 1
STAGE_QUALIFICATION = 2

now = datetime.datetime.now()
company_name = env.company.name or 'Our Company'
base_url = env['ir.config_parameter'].sudo().get_param('web.base.url', '')

# ── Resolve notification recipients (HR Recruitment Manager group) ──
hr_group = env.ref('hr_recruitment.group_hr_recruitment_manager', raise_if_not_found=False)
notify_partners = hr_group.user_ids.filtered('active').mapped('partner_id') if hr_group else env['res.partner']

body = ""
total_count = 0

# ═══════════════════════════════════════════════════
# SECTION 1: Qualification Stage — Info Survey Pending
# ═══════════════════════════════════════════════════
qual_candidates = env['hr.applicant'].search([
    ('active', '=', True),
    ('stage_id', '=', STAGE_QUALIFICATION),
    ('x_studio_s1_reminder_count', '>=', 1),
    ('x_studio_sms_sent', '=', False),
])

if qual_candidates:
    total_count += len(qual_candidates)
    sms_entries = []
    for r in qual_candidates:
        recruiter_name = "the %s Recruitment Team" % company_name
        if r.user_id and r.user_id.name:
            recruiter_name = r.user_id.name.split(' ')[0]

        phone = r.partner_phone or '(no phone on file)'

        first_name = (r.partner_name or 'Applicant').split(' ')[0]
        sms_text = (
            "Hello %s, this is %s from %s. "
            "We sent you an email with an information form for the %s position. "
            "Kindly complete it at your earliest convenience so we can proceed with your application. "
            "Let us know if you need any help! - %s Recruitment Team"
        ) % (first_name, recruiter_name, company_name, r.job_id.name or 'open', company_name)

        link = "%s/odoo/recruitment-applications/%s" % (base_url, r.id)
        sms_entries.append(
            "<tr>"
            "<td><a href='%s'><b>%s</b></a></td>"
            "<td>%s</td>"
            "<td>%s</td>"
            "<td style='font-family:monospace;font-size:0.85em;'>%s</td>"
            "</tr>" % (link, r.partner_name or 'Unknown', r.job_id.name or '', phone, sms_text)
        )

    body += "<h3>Section 1: Info Survey Pending (%s candidate(s))</h3>" % len(qual_candidates)
    body += "<p>These candidates have not responded to their email reminder for the info survey.</p>"
    body += "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse:collapse;width:100%'>"
    body += "<thead><tr><th>Candidate</th><th>Job</th><th>Phone</th><th>SMS Text (Copy & Paste)</th></tr></thead>"
    body += "<tbody>" + "".join(sms_entries) + "</tbody></table>"

# ═══════════════════════════════════════════════════
# SECTION 2: Resume Missing — Stage 1
# ═══════════════════════════════════════════════════
resume_candidates = env['hr.applicant'].search([
    ('active', '=', True),
    ('stage_id', '=', STAGE_NEW),
    ('x_studio_s1_reminder_count', '>=', 1),
    ('x_studio_sms_sent', '=', False),
]).filtered(lambda r: r.attachment_number == 0)

if resume_candidates:
    total_count += len(resume_candidates)
    sms_entries = []
    for r in resume_candidates:
        recruiter_name = "the %s Recruitment Team" % company_name
        if r.user_id and r.user_id.name:
            recruiter_name = r.user_id.name.split(' ')[0]

        phone = r.partner_phone or '(no phone on file)'

        first_name = (r.partner_name or 'Applicant').split(' ')[0]
        sms_text = (
            "Hi %s, this is %s from %s. "
            "We noticed your application for the %s position is missing a resume/CV. "
            "Kindly reply to the email we sent or send your resume to this number. "
            "Thank you! - %s Recruitment Team"
        ) % (first_name, recruiter_name, company_name, r.job_id.name or 'open', company_name)

        link = "%s/odoo/recruitment-applications/%s" % (base_url, r.id)
        sms_entries.append(
            "<tr>"
            "<td><a href='%s'><b>%s</b></a></td>"
            "<td>%s</td>"
            "<td>%s</td>"
            "<td style='font-family:monospace;font-size:0.85em;'>%s</td>"
            "</tr>" % (link, r.partner_name or 'Unknown', r.job_id.name or '', phone, sms_text)
        )

    body += "<h3>Section 2: Resume Missing (%s candidate(s))</h3>" % len(resume_candidates)
    body += "<p>These candidates in Stage 1 have been reminded but still have no resume on file.</p>"
    body += "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse:collapse;width:100%'>"
    body += "<thead><tr><th>Candidate</th><th>Job</th><th>Phone</th><th>SMS Text (Copy & Paste)</th></tr></thead>"
    body += "<tbody>" + "".join(sms_entries) + "</tbody></table>"

# ═══════════════════════════════════════════════════
# SEND COMBINED REPORT
# ═══════════════════════════════════════════════════
if total_count > 0 and notify_partners:
    subject = "%s SMS Action Queue: %s Candidate(s) Need Follow-up" % (company_name, total_count)
    header = "<h2>%s Daily SMS Action Queue</h2>" % company_name
    header += "<p>Please send the SMS below to each candidate, then check the <b>'SMS Sent'</b> box on their Odoo profile.</p>"

    # Use mail.mail for proper HTML rendering (message_notify escapes HTML in SaaS safe_eval)
    env['mail.mail'].sudo().create({
        'subject': subject,
        'body_html': header + body,
        'recipient_ids': [(4, p) for p in notify_partners.ids],
        'auto_delete': True,
    }).send()
