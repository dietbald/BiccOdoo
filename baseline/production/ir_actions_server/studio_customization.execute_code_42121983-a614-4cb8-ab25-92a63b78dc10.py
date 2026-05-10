if record:
    record.write({'stage_id': 2})
    record.message_post(
        body=f"N8N update Applicant stage to Screened",
        message_type='comment',
    )
