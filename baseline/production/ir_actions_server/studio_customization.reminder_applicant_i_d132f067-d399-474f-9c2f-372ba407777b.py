template_id = 102
email_template = env["mail.template"].browse(template_id)

now = datetime.datetime.now()
cutoff = now - datetime.timedelta(days=4)  # send reminder 1 after 2 days (adjust)

for applicant in records:
    # Skip if no email
    if not applicant.email_from:
        raise UserError("Applicant needs a valid email")
        continue
    
    if not applicant.x_studio_reminder_sent:
        raise UserError("Sent a first reminder first")
        continue
    
    if applicant.x_studio_final_reminder_sent:
        raise UserError("Final Reminder already sent")
        continue
    
        # Get the survey from the job position
    if not applicant.job_id:
        raise UserError("Applicant has no Job Position set: %s (ID %s)" % (applicant.display_name, applicant.id))

    survey = applicant.job_id.x_studio_application_information
    if not survey:
        raise UserError(
            "Job Position '%s' has no Application Information survey set (field x_studio_application_information). Applicant: %s (ID %s)"
            % (applicant.job_id.name, applicant.display_name, applicant.id)
        )

    # Optional: validate survey config
    try:
        survey.check_validity()
    except Exception as e:
        raise UserError("Survey is not valid for job '%s'. Error: %s" % (applicant.job_id.name, str(e)))

    survey_id = survey.id
    
    # do not remind if already completed
    done_input = env["survey.user_input"].search([
        ("survey_id", "=", survey_id),
        ("applicant_id", "=", applicant.id),
        ("state", "=", "done"),
    ], limit=1)
    if done_input:
        raise UserError("Survey already completed")
        continue
    
    user_input = env["survey.user_input"].search([
        ("survey_id", "=", survey_id),
        ("applicant_id", "=", applicant.id),
    ], order="create_date desc", limit=1)

    # If none exists, skip
    if not user_input:
        raise UserError("Survey was not sent")
        continue

    # Optional gating: only remind if the user_input is old enough
    if user_input.create_date and user_input.create_date > cutoff:
        raise UserError("Reminders should be sent only after 48 hours")
        continue

    survey_link = user_input.get_start_url()

    ctx = dict(env.context or {})
    ctx.update({"survey_link": survey_link})

    if email_template:
        email_template.with_context(ctx).send_mail(applicant.id, force_send=False)
        applicant.write({
            "x_studio_final_reminder_sent": True,
        })
        applicant.message_post(body="Survey Final reminder sent.")
