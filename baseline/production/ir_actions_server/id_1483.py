# Define the survey ID
survey_id = 62  # Ensure this matches the actual survey ID in Odoo

# Define mapping between survey questions and applicant fields
# CHANGED: For Expected Salary, use "char_box" instead of "number" because the survey question expects text.
question_mapping = {
    "Full Name": ("display_name", "char_box"),  # using display_name for full name
    "What is the best phone number to reach you for a phone interview?": ("partner_phone", "char_box"),  # using partner_phone for phone number
   
}

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

    # Get all survey questions for the survey
    survey_questions = env["survey.question"].search([("survey_id", "=", survey_id)])

    # Prepare answer records list
    answers = []

    for question in survey_questions:
        # Check if the question title matches one in our mapping
        if question.title in question_mapping:
            field_name, field_type = question_mapping[question.title]
            # Use dictionary-style access for safety
            prefill_value = applicant[field_name] if applicant[field_name] else ""
            if prefill_value:
                answer_record = {
                    "user_input_id": user_input.id,
                    "question_id": question.id,
                }
                # For numerical fields, if any, you could use "number" and "value_number"
                if field_type == "number":
                    answer_record["answer_type"] = "numerical_box"
                    answer_record["value_number"] = float(prefill_value)
                else:
                    # Use "char_box" as the answer type and corresponding key "value_char_box"
                    answer_record["answer_type"] = "char_box"
                    answer_record["value_char_box"] = prefill_value

                answers.append((0, 0, answer_record))

    # Write prefilled answers to the survey response
    if answers:
        user_input.write({"user_input_line_ids": answers})

    applicant.message_post(body=user_input.state)

    # Send the survey invitation email using your custom email template
    email_template = env.ref("__custom__.survey.email_template_applicant_information")
    if email_template:
        res = email_template.send_mail(user_input.id, force_send=True)
        
        # Extract the generated email body from mail.mail
        mail_record = env['mail.mail'].search([
            ('mail_message_id', '=', res)
        ], order="id desc", limit=1)
        applicant.message_post(body=res)
        if mail_record and mail_record.body_html:
            # Post the rendered email content in the chatter
            applicant.message_post(body=mail_record.body_html)


        
