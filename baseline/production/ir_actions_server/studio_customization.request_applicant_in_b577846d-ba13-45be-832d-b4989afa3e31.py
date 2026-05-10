
template_id = 101
email_template = env["mail.template"].browse(template_id)

now = datetime.datetime.now()
cutoff = now - datetime.timedelta(days=2)  # send reminder 1 after 2 days (adjust)

for applicant in records:
    # Skip if no email
    if not applicant.email_from:
        applicant.message_post(body="No Email")
        continue
    
    if applicant.x_studio_reminder_sent:
        applicant.message_post(body="Reminder already sent")
        continue

    # Get the survey from the job position
    if not applicant.job_id:
        applicant.message_post("Applicant has no Job Position set: %s (ID %s)" % (applicant.display_name, applicant.id))

    survey = applicant.job_id.x_studio_application_information
    if not survey:
       applicant.message_post(
            "Job Position '%s' has no Application Information survey set (field x_studio_application_information). Applicant: %s (ID %s)"
            % (applicant.job_id.name, applicant.display_name, applicant.id)
        )

    # Optional: validate survey config
    try:
        survey.check_validity()
    except Exception as e:
        applicant.message_post("Survey is not valid for job '%s'. Error: %s" % (applicant.job_id.name, str(e)))

    survey_id = survey.id

    # do not remind if already completed
    done_input = env["survey.user_input"].search([
        ("survey_id", "=", survey_id),
        ("applicant_id", "=", applicant.id),
        ("state", "=", "done"),
    ], limit=1)
    if done_input:
        applicant.message_post(body="Survey submitted")
        continue

    user_input = env["survey.user_input"].search([
        ("survey_id", "=", survey_id),
        ("applicant_id", "=", applicant.id),
    ], order="create_date desc", limit=1)

    # If none exists, skip
    if not user_input:
        applicant.message_post(body="No Survey sent")
        continue

    # Optional gating: only remind if the user_input is old enough
    if user_input.create_date and user_input.create_date > cutoff:
        applicant.message_post(body="Too early to remind them")
        continue

    survey_link = user_input.get_start_url()

    ctx = dict(env.context or {})
    ctx.update({"survey_link": survey_link})

    if email_template:
        email_template.with_context(ctx).send_mail(applicant.id, force_send=False)
        applicant.write({
            "x_studio_reminder_sent": True,
        })
        try:
            applicant.message_post(body="Survey reminder 1 sent.")
        except Exception:
            pass
