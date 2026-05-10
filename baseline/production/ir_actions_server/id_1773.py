# Model: hr.applicant
# Run on selected applicants (or filtered list)



template_id = 103  # <-- replace with your mail.template ID
template = env["mail.template"].browse(template_id)
if not template:
    raise Exception("Missing email template: mail_template_recruitment.mail_template_applicant_information_resend")

for applicant in records:
    if not applicant.job_id:
        raise Exception("Applicant has no job position: %s (ID %s)" % (applicant.display_name, applicant.id))

    survey = applicant.job_id.x_studio_application_information
    if not survey:
        raise Exception("Job Position '%s' has no Application Information survey set (x_studio_application_information)." % (applicant.job_id.name or "Unknown"))

    # Require email
    if not applicant.email_from:
        # don't stop whole batch for missing email; just skip
        try:
            applicant.message_post(body="RESEND INFO FORM NOT SENT: applicant email is missing.")
        except Exception:
            pass
        continue
  
    # If already completed, skip
    done_input = env["survey.user_input"].search([
        ("survey_id", "=", survey.id),
        ("applicant_id", "=", applicant.id),
        ("state", "=", "done"),
    ], limit=1)
    if done_input:
        applicant.message_post(body="Application information already completed")
        continue

    # Create a fresh user_input (new link)
    user_input = env["survey.user_input"].create({
        "survey_id": survey.id,
        "partner_id": applicant.partner_id.id if applicant.partner_id else False,
        "email": applicant.email_from,
        "applicant_id": applicant.id,
        "state": "new",
    })

    ctx = dict(env.context or {})
    ctx.update({"survey_link": user_input.get_start_url()})

    template.with_context(ctx).send_mail(applicant.id, force_send=False)

    # Optional log (wrapped to avoid your chatter sort crash issue)
    try:
        applicant.message_post(body="Application information form resent (new link generated).")
    except Exception:
        pass
