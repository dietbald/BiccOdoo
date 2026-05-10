# Server Action — Send Assessment Reminder (NO new surveys created)
# Model: hr.applicant
# Uses template: mail_template_recruitment.mail_template_applicant_reminder
# Expects ctx keys: logical_test, emotional_test, technical_test, deadline

template = env.ref("mail_template_recruitment.mail_template_applicant_reminder", raise_if_not_found=False)

for applicant in records:

    # Basic validations
    if not applicant.job_id:
        applicant.message_post(body="Reminder not sent: no job position on this application.")
        continue

    job = applicant.job_id
    technical_survey = job.survey_id
    logical_survey = job.x_studio_logical_assessment
    emotional_survey = job.x_studio_emotional_assessment

    missing_surveys = []
    if not technical_survey:
        missing_surveys.append("technical")
    if not logical_survey:
        missing_surveys.append("logical")
    if not emotional_survey:
        missing_surveys.append("emotional")

    if missing_surveys:
        applicant.message_post(body="Reminder not sent: missing job surveys (%s)." % ", ".join(missing_surveys))
        continue

    if not applicant.partner_id:
        applicant.message_post(body="Reminder not sent: applicant has no partner_id.")
        continue

    if not template:
        applicant.message_post(body="Reminder not sent: reminder email template not found.")
        continue

    # Helper: fetch EXISTING user_input (do not create)
    def _pending_user_input(survey):
        return env["survey.user_input"].search([
            ("survey_id", "=", survey.id),
            ("applicant_id", "=", applicant.id),
            ("partner_id", "=", applicant.partner_id.id),
            ("state", "!=", "done"),
        ], limit=1)

    technical_ui = _pending_user_input(technical_survey)
    logical_ui = _pending_user_input(logical_survey)
    emotional_ui = _pending_user_input(emotional_survey)

    missing_links = []
    if not logical_ui:
        missing_links.append("logical link")
    if not emotional_ui:
        missing_links.append("emotional link")
    if not technical_ui:
        missing_links.append("technical link")

    if missing_links:
        applicant.message_post(
            body="Reminder not sent: no existing pending assessment link(s) found (%s)."
                 % ", ".join(missing_links)
        )
        continue

    # Deadline: use the earliest existing deadline, fallback to +7 days
    deadlines = []
    if logical_ui.deadline:
        deadlines.append(logical_ui.deadline)
    if emotional_ui.deadline:
        deadlines.append(emotional_ui.deadline)
    if technical_ui.deadline:
        deadlines.append(technical_ui.deadline)

    deadline = min(deadlines) if deadlines else (datetime.datetime.now() + datetime.timedelta(days=7))

    # Context for template
    ctx = dict(
        logical_test=logical_ui.get_start_url(),
        emotional_test=emotional_ui.get_start_url(),
        technical_test=technical_ui.get_start_url(),
        deadline=deadline,
    )

    # Force recipient to applicant email (prevents any misrouting)
    email_to = (applicant.email_from or "").strip() or (applicant.partner_id.email or "").strip()
    if not email_to:
        applicant.message_post(body="Reminder not sent: applicant has no email (email_from / partner.email empty).")
        continue

    email_values = {
        "email_to": email_to,
        # Clear recipients in case template defaults add partner recipients
        "recipient_ids": [],
    }

    # Queue email
    mail_id = template.with_context(ctx).send_mail(applicant.id, force_send=False, email_values=email_values)

    if mail_id:
        mail = env["mail.mail"].browse(mail_id)
        applicant.message_post(
            subtype_xmlid="mail.mt_note",
            body=(
                "<b>Assessment reminder queued</b><br/>"
                f"<b>To:</b> {mail.email_to or ''}<br/>"
                f"<b>Subject:</b> {mail.subject or ''}<br/>"
                f"<b>Deadline:</b> {deadline}"
            ),
        )
    else:
        applicant.message_post(body="Reminder not sent: send_mail did not return a mail_id.")