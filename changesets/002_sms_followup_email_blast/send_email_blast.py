# TRIGGER: Manual button on hr.applicant (Action menu / gear icon)
# MODEL: hr.applicant
# DESCRIPTION: Send a follow-up email to all applicants currently in the
#   "SMS follow-up queue" — i.e. the same three populations that
#   action_sms_queue_digest.py surfaces for HR to SMS manually.
#   Voice mirrors the SMS wording: short, first-name greeting, identifies
#   the company and the role, gives a "if you didn't get our email" out.
#
# Behaviour:
#   - Reads the applicant lists by introspecting fields at runtime (so the
#     action is safe to deploy before all the v5 field blocks land — it just
#     no-ops the section whose driving field doesn't exist yet).
#   - Sends one mail.mail per applicant; chatter is updated with a MANUAL
#     ACTION line so HR can audit what was sent.
#   - Does NOT stamp x_studio_sms_*_date fields. SMS is a separate channel;
#     HR may still want to SMS the same population.
#   - Runs across all queue populations regardless of which records HR had
#     selected in the list view — this is a "blast" action by design.

STAGE_NEW = 1
STAGE_QUALIFICATION = 2
STAGE_ASSESSMENT_SENT = 7


def field_exists(model_name, field_name):
    return bool(env['ir.model.fields'].sudo().search([
        ('model', '=', model_name),
        ('name', '=', field_name),
    ], limit=1))


def applicant_email_body(applicant, kind):
    short = applicant.company_id.x_studio_short_name if hasattr(applicant.company_id, 'x_studio_short_name') else False
    co = short or (applicant.company_id.name if applicant.company_id else 'Our Company')
    first_name = (applicant.partner_name or 'there').split(' ')[0]
    job = applicant.job_id.name if applicant.job_id else 'open'

    if kind == 'qualification':
        subject = "Following up on your %s application" % job
        body = (
            "<p>Hi %s,</p>"
            "<p>This is %s HR. We sent you the Applicant Information form for the "
            "<b>%s</b> role a few days back. Could you fill it out so we can keep "
            "things moving?</p>"
            "<p>If you didn't get our email, let us know and we'll resend.</p>"
            "<p>Thanks,<br/>%s Recruitment Team</p>"
        ) % (first_name, co, job, co)
    elif kind == 'resume':
        subject = "Following up on your %s application" % job
        body = (
            "<p>Hi %s,</p>"
            "<p>This is %s HR. We got your application for the <b>%s</b> role but "
            "didn't see a resume attached. Could you reply to our email with it?</p>"
            "<p>If you never got our email, let us know.</p>"
            "<p>Thanks,<br/>%s Recruitment Team</p>"
        ) % (first_name, co, job, co)
    else:  # assessment
        subject = "Following up on your %s assessment" % job
        body = (
            "<p>Hi %s,</p>"
            "<p>%s HR here. Have you had a chance to do the assessment we emailed "
            "you for the <b>%s</b> role? Please send it back when you can.</p>"
            "<p>If you can't find our email, let us know.</p>"
            "<p>Thanks,<br/>%s Recruitment Team</p>"
        ) % (first_name, co, job, co)
    return subject, body


def send_one(applicant, kind):
    if not applicant.email_from:
        applicant.message_post(body="SKIP: no email on file — cannot send follow-up.")
        return False
    subject, body_html = applicant_email_body(applicant, kind)
    env['mail.mail'].sudo().create({
        'subject': subject,
        'body_html': body_html,
        'email_to': applicant.email_from,
        'auto_delete': True,
    }).send()
    applicant.message_post(
        body="MANUAL ACTION: Follow-up email sent (%s queue)." % kind
    )
    return True


sent_qual = 0
sent_resume = 0
sent_assess = 0

# ── Section 1: Qualification (Stage 2) — info-survey pending ────────────────
if (field_exists('hr.applicant', 'x_studio_reminder_date')
        and field_exists('hr.applicant', 'x_studio_sms_reminder_date')):
    qual = env['hr.applicant'].search([
        ('active', '=', True),
        ('stage_id', '=', STAGE_QUALIFICATION),
        ('x_studio_reminder_date', '!=', False),
        ('x_studio_sms_reminder_date', '=', False),
    ])
    for r in qual:
        if send_one(r, 'qualification'):
            sent_qual += 1

# ── Section 2: Resume Missing (Stage 1) ─────────────────────────────────────
if (field_exists('hr.applicant', 'x_studio_resume_request_date')
        and field_exists('hr.applicant', 'x_studio_sms_new_reminder_date')):
    resume = env['hr.applicant'].search([
        ('active', '=', True),
        ('stage_id', '=', STAGE_NEW),
        ('x_studio_resume_request_date', '!=', False),
        ('x_studio_sms_new_reminder_date', '=', False),
    ]).filtered(lambda r: r.attachment_number == 0)
    for r in resume:
        if send_one(r, 'resume'):
            sent_resume += 1

# ── Section 3: Assessment (Stage 7) — assessment pending ────────────────────
if field_exists('hr.applicant', 'x_studio_assessment_final_reminder_date'):
    asses = env['hr.applicant'].search([
        ('active', '=', True),
        ('stage_id', '=', STAGE_ASSESSMENT_SENT),
        ('x_studio_assessment_final_reminder_date', '!=', False),
    ])
    for r in asses:
        if send_one(r, 'assessment'):
            sent_assess += 1

log("Follow-up email blast complete: qual=%d resume=%d assessment=%d (total=%d)" % (
    sent_qual, sent_resume, sent_assess, sent_qual + sent_resume + sent_assess
))
