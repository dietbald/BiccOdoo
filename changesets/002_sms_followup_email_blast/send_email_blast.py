# TRIGGER: Manual button on hr.applicant (Action menu)
# MODEL: hr.applicant
# DESCRIPTION: Email the HR Recruitment Manager group a single digest of every
#   applicant who needs an SMS follow-up right now. Each section is a
#   3-column table (Applicant name with link, mobile number, ready-to-send
#   SMS text). HR sends the SMSes from their phone and updates the
#   corresponding x_studio_sms_*_date field once delivered.

STAGE_NEW = 1
STAGE_QUALIFICATION = 2
STAGE_ASSESSMENT_SENT = 7

base_url = env['ir.config_parameter'].sudo().get_param('web.base.url', '')


def field_exists(model_name, field_name):
    return bool(env['ir.model.fields'].sudo().search([
        ('model', '=', model_name),
        ('name', '=', field_name),
    ], limit=1))


def applicant_co(applicant):
    short = False
    if applicant.company_id and hasattr(applicant.company_id, 'x_studio_short_name'):
        short = applicant.company_id.x_studio_short_name
    return short or (applicant.company_id.name if applicant.company_id else 'BICC')


def sms_text(applicant, kind):
    co = applicant_co(applicant)
    first_name = (applicant.partner_name or 'there').split(' ')[0]
    job = applicant.job_id.name if applicant.job_id else 'open'
    if kind == 'qualification':
        return (
            "Hi %s, this is %s HR. We sent you the Applicant Information form "
            "for the %s role a few days back. Could you fill it out so we can "
            "keep things moving? If you didn't get our email, let us know."
        ) % (first_name, co, job)
    if kind == 'resume':
        return (
            "Hi %s, %s HR here. We got your application for the %s role but "
            "didn't see a resume attached. Could you reply to our email with it? "
            "If you never got our email, let us know."
        ) % (first_name, co, job)
    # assessment
    return (
        "Hi %s, %s HR here. Have you had a chance to do the assessment we "
        "emailed you for the %s role? Please send it back when you can. "
        "If you can't find our email, let us know."
    ) % (first_name, co, job)


def render_row(applicant, message):
    name = applicant.partner_name or 'Unknown'
    link = "%s/odoo/recruitment-applications/%s" % (base_url, applicant.id)
    phone = applicant.partner_phone or '(no phone on file)'
    return (
        "<tr>"
        "<td><a href='%s'><b>%s</b></a></td>"
        "<td>%s</td>"
        "<td style='font-family:monospace;font-size:0.88em;white-space:pre-wrap;'>%s</td>"
        "</tr>"
    ) % (link, name, phone, message)


def render_section(title, applicants, kind):
    rows = "".join(render_row(r, sms_text(r, kind)) for r in applicants)
    return (
        "<h3 style='margin-top:24px;'>%s (%d candidate(s))</h3>"
        "<table border='1' cellpadding='8' cellspacing='0' "
        "style='border-collapse:collapse;width:100%%;'>"
        "<thead style='background:#f2f2f2;'><tr>"
        "<th align='left'>Applicant</th>"
        "<th align='left'>Mobile</th>"
        "<th align='left'>SMS to send</th>"
        "</tr></thead>"
        "<tbody>%s</tbody>"
        "</table>"
    ) % (title, len(applicants), rows)


sections = []
total = 0

# ── Qualification (Stage 2) — info survey pending after reminder ────────────
if (field_exists('hr.applicant', 'x_studio_reminder_date')
        and field_exists('hr.applicant', 'x_studio_sms_reminder_date')):
    qual = env['hr.applicant'].search([
        ('active', '=', True),
        ('stage_id', '=', STAGE_QUALIFICATION),
        ('x_studio_reminder_date', '!=', False),
        ('x_studio_sms_reminder_date', '=', False),
    ])
    if qual:
        total += len(qual)
        sections.append(render_section(
            'Qualification &mdash; Info Survey Pending', qual, 'qualification'
        ))

# ── Resume Missing (Stage 1) ────────────────────────────────────────────────
if (field_exists('hr.applicant', 'x_studio_resume_request_date')
        and field_exists('hr.applicant', 'x_studio_sms_new_reminder_date')):
    resume = env['hr.applicant'].search([
        ('active', '=', True),
        ('stage_id', '=', STAGE_NEW),
        ('x_studio_resume_request_date', '!=', False),
        ('x_studio_sms_new_reminder_date', '=', False),
    ]).filtered(lambda r: r.attachment_number == 0)
    if resume:
        total += len(resume)
        sections.append(render_section('Resume Missing', resume, 'resume'))

# ── Assessment (Stage 7) — assessment pending after final reminder ──────────
if field_exists('hr.applicant', 'x_studio_assessment_final_reminder_date'):
    asses = env['hr.applicant'].search([
        ('active', '=', True),
        ('stage_id', '=', STAGE_ASSESSMENT_SENT),
        ('x_studio_assessment_final_reminder_date', '!=', False),
    ])
    if asses:
        total += len(asses)
        sections.append(render_section(
            'Assessment &mdash; Awaiting Completion', asses, 'assessment'
        ))

# ── Resolve HR recipients ───────────────────────────────────────────────────
hr_group = env.ref('hr_recruitment.group_hr_recruitment_manager', raise_if_not_found=False)
notify_partners = hr_group.user_ids.filtered('active').mapped('partner_id') if hr_group else env['res.partner']

company_name = env.company.name if env.company else 'BICC'

if total > 0 and notify_partners:
    subject = "%s SMS Queue: %d candidate(s) need a follow-up SMS" % (company_name, total)
    header = (
        "<h2 style='color:#101820;'>%s SMS Queue (manual request)</h2>"
        "<p>Each row below is one candidate. Copy the <b>SMS to send</b> column "
        "into your phone, text it to the matching number, then mark the SMS "
        "reminder date on the applicant record so the queue clears.</p>"
    ) % company_name
    env['mail.mail'].sudo().create({
        'subject': subject,
        'body_html': header + "".join(sections),
        'recipient_ids': [(4, p) for p in notify_partners.ids],
        'auto_delete': True,
    }).send()
    log("SMS queue digest sent: %d candidate(s) across %d section(s)" % (total, len(sections)))
elif total == 0:
    log("SMS queue digest: nothing to send — queue is empty.")
else:
    log("SMS queue digest: %d candidate(s) ready but no HR recipients resolved." % total)
