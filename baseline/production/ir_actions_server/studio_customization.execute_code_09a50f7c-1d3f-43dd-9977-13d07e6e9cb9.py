for record in records:
    applicant = record.applicant_id
    if not applicant:
        continue

    survey = applicant.job_id.x_studio_application_information
    if not survey:
        applicant.message_post(body="Applicant information not set.")
        continue

    if record.survey_id.id != survey.id:
        continue

    if record.state != "done":
        continue

    applicant.message_post(body="Applicant information form completed.")
