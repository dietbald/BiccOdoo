# TRIGGER: Manual button on hr.applicant (Action menu)
# MODEL: hr.applicant
# DESCRIPTION: Email the HR Recruitment Manager group a single digest of every
#   applicant who needs an SMS follow-up right now, grouped by job position.
#   For each job there is ONE table with three columns (Applicant name with
#   link, mobile number, ready-to-send SMS text). The SMS wording depends on
#   which queue the applicant is in (qualification / resume / assessment) and
#   is pre-filled per candidate so HR copies it straight into their phone.
#
# Pattern note: Odoo SaaS safe_eval forbids closures (LOAD_CLOSURE / MAKE_CELL)
# inside lambdas / comprehensions / nested defs. Everything below is plain
# procedural — no nested def, no genexp closing over outer-scope variables.

STAGE_NEW = 1
STAGE_QUALIFICATION = 2
STAGE_ASSESSMENT_SENT = 7

base_url = env['ir.config_parameter'].sudo().get_param('web.base.url', '')
company_name = env.company.name if env.company else 'BICC'

# Field-availability flags (driving fields for each section).
fld = env['ir.model.fields'].sudo()
has_qual_fields = (
    bool(fld.search([('model', '=', 'hr.applicant'), ('name', '=', 'x_studio_reminder_date')], limit=1))
    and bool(fld.search([('model', '=', 'hr.applicant'), ('name', '=', 'x_studio_sms_reminder_date')], limit=1))
)
has_resume_fields = (
    bool(fld.search([('model', '=', 'hr.applicant'), ('name', '=', 'x_studio_resume_request_date')], limit=1))
    and bool(fld.search([('model', '=', 'hr.applicant'), ('name', '=', 'x_studio_sms_new_reminder_date')], limit=1))
)
has_assessment_field = bool(
    fld.search([('model', '=', 'hr.applicant'), ('name', '=', 'x_studio_assessment_final_reminder_date')], limit=1)
)
has_short_name = bool(
    fld.search([('model', '=', 'res.company'), ('name', '=', 'x_studio_short_name')], limit=1)
)


# Flat list of (applicant, sms_message_string). We compute the SMS text per
# candidate while iterating the source queue (so the kind-specific wording is
# captured in the string itself; no need to track "kind" downstream).
entries = []


# ── Queue 1: Qualification (Stage 2) ───────────────────────────────────────
if has_qual_fields:
    qual_candidates = env['hr.applicant'].search([
        ('active', '=', True),
        ('stage_id', '=', STAGE_QUALIFICATION),
        ('x_studio_reminder_date', '!=', False),
        ('x_studio_sms_reminder_date', '=', False),
    ])
    for r in qual_candidates:
        co_short = False
        if r.company_id and has_short_name:
            co_short = r.company_id.x_studio_short_name
        co = co_short or (r.company_id.name if r.company_id else 'BICC')
        first_name = (r.partner_name or 'there').split(' ')[0]
        job = r.job_id.name if r.job_id else 'open'
        message = (
            "Hi %s, this is %s HR. We sent you the Applicant Information form "
            "for the %s role a few days back. Could you fill it out so we can "
            "keep things moving? If you didn't get our email, let us know."
        ) % (first_name, co, job)
        entries.append((r, message))


# ── Queue 2: Resume Missing (Stage 1) ──────────────────────────────────────
if has_resume_fields:
    resume_pool = env['hr.applicant'].search([
        ('active', '=', True),
        ('stage_id', '=', STAGE_NEW),
        ('x_studio_resume_request_date', '!=', False),
        ('x_studio_sms_new_reminder_date', '=', False),
    ])
    resume_ids = []
    for r in resume_pool:
        if r.attachment_number == 0:
            resume_ids.append(r.id)
    resume_candidates = env['hr.applicant'].browse(resume_ids)
    for r in resume_candidates:
        co_short = False
        if r.company_id and has_short_name:
            co_short = r.company_id.x_studio_short_name
        co = co_short or (r.company_id.name if r.company_id else 'BICC')
        first_name = (r.partner_name or 'there').split(' ')[0]
        job = r.job_id.name if r.job_id else 'open'
        message = (
            "Hi %s, %s HR here. We got your application for the %s role but "
            "didn't see a resume attached. Could you reply to our email with it? "
            "If you never got our email, let us know."
        ) % (first_name, co, job)
        entries.append((r, message))


# ── Queue 3: Assessment (Stage 7) ──────────────────────────────────────────
if has_assessment_field:
    asses_candidates = env['hr.applicant'].search([
        ('active', '=', True),
        ('stage_id', '=', STAGE_ASSESSMENT_SENT),
        ('x_studio_assessment_final_reminder_date', '!=', False),
    ])
    for r in asses_candidates:
        co_short = False
        if r.company_id and has_short_name:
            co_short = r.company_id.x_studio_short_name
        co = co_short or (r.company_id.name if r.company_id else 'BICC')
        first_name = (r.partner_name or 'there').split(' ')[0]
        job = r.job_id.name if r.job_id else 'open'
        message = (
            "Hi %s, %s HR here. Have you had a chance to do the assessment we "
            "emailed you for the %s role? Please send it back when you can. "
            "If you can't find our email, let us know."
        ) % (first_name, co, job)
        entries.append((r, message))


# ── Group by job, then render ──────────────────────────────────────────────
groups = {}  # job_label → list of (applicant, message)
for applicant, message in entries:
    job_label = applicant.job_id.name if applicant.job_id else '(No job position)'
    if job_label not in groups:
        groups[job_label] = []
    groups[job_label].append((applicant, message))

# Sort job labels alphabetically; "(No job position)" sorts to the end of the
# list because of the leading '(' — fine, it lands as a final catch-all section.
job_labels = list(groups.keys())
job_labels.sort()

sections_html = ""
total_count = len(entries)

for job_label in job_labels:
    job_entries = groups[job_label]
    rows_html = ""
    for applicant, message in job_entries:
        name = applicant.partner_name or 'Unknown'
        link = "%s/odoo/recruitment-applications/%s" % (base_url, applicant.id)
        phone = applicant.partner_phone or '(no phone on file)'
        rows_html += (
            "<tr>"
            "<td><a href='%s'><b>%s</b></a></td>"
            "<td>%s</td>"
            "<td style='font-family:monospace;font-size:0.88em;white-space:pre-wrap;'>%s</td>"
            "</tr>"
        ) % (link, name, phone, message)

    sections_html += (
        "<h3 style='margin-top:24px;color:#101820;'>%s (%d candidate(s))</h3>"
        "<table border='1' cellpadding='8' cellspacing='0' "
        "style='border-collapse:collapse;width:100%%;'>"
        "<thead style='background:#f2f2f2;'><tr>"
        "<th align='left'>Applicant</th>"
        "<th align='left'>Mobile</th>"
        "<th align='left'>SMS to send</th>"
        "</tr></thead>"
        "<tbody>%s</tbody>"
        "</table>"
    ) % (job_label, len(job_entries), rows_html)


# ── Resolve HR recipients ──────────────────────────────────────────────────
hr_group = env.ref('hr_recruitment.group_hr_recruitment_manager', raise_if_not_found=False)
notify_partners = env['res.partner']
if hr_group:
    notify_partners = hr_group.user_ids.filtered('active').mapped('partner_id')


# ── Send (or log no-op) ────────────────────────────────────────────────────
if total_count > 0 and notify_partners:
    subject = "%s SMS Queue: %d candidate(s) need a follow-up SMS" % (company_name, total_count)
    header = (
        "<h2 style='color:#101820;'>%s SMS Queue (manual request)</h2>"
        "<p>Below is one section per job position with the candidates who need "
        "an SMS follow-up right now. Copy the <b>SMS to send</b> column into "
        "your phone, text it to the matching number, then mark the SMS "
        "reminder date on the applicant record so the queue clears.</p>"
    ) % company_name

    recipient_cmds = []
    for pid in notify_partners.ids:
        recipient_cmds.append((4, pid))

    env['mail.mail'].sudo().create({
        'subject': subject,
        'body_html': header + sections_html,
        'recipient_ids': recipient_cmds,
        'auto_delete': True,
    }).send()
    log("SMS queue digest sent: %d candidate(s) across %d job position(s)." % (total_count, len(job_labels)))
elif total_count == 0:
    log("SMS queue digest: nothing to send (queue empty).")
else:
    log("SMS queue digest: %d candidate(s) ready but no HR recipients resolved." % total_count)
