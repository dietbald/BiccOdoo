# Define the survey ID
survey_id = 94  # Ensure this matches the actual survey ID in Odoo


# Loop through selected applicants
for applicant in records:
    # Create a new survey user input entry for the applicant
    user_input = env["survey.user_input"].create({
        "survey_id": survey_id,
        "partner_id": applicant.partner_id.id if applicant.partner_id else False,
        "email": applicant.email_from,
        "applicant_id": applicant.id,  # Ensure the applicant is linked!
        "state": "new",
    })

    # Send the survey invitation email using your custom email template
    #email_template = env.ref("__custom__.survey.email_template_applicant_information")
    email_template = env['mail.template'].browse(79)
    
    custom_ctx = {
        'survey_link': user_input.get_start_url(),
    }
    email_template = email_template.with_context(custom_ctx)
    
    if email_template:
        mail_id = email_template.send_mail(applicant.id, force_send=False)
        applicant.message_post(body="Request Applicant Information sent")  
    else:
        applicant.message_post(body="Request Applicant Information NOT sent")
    
    applicant.write({'kanban_state': 'blocked'})