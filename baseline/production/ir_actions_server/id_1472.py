# Example: Extend deadline by 7 days
new_deadline = datetime.datetime.now() + datetime.timedelta(days=7)

for record in records:
    # Search all user_input records linked to this applicant
    user_inputs = env['survey.user_input'].search([
        ('applicant_id', '=', record.id)
    ])
    if user_inputs:
        user_inputs.write({'deadline': new_deadline})
