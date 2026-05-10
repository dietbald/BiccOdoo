# Available variables:
#  - env: environment on which the action is triggered
#  - model: model of the record on which the action is triggered; is a void recordset
#  - record: record on which the action is triggered; may be void
#  - records: recordset of all records on which the action is triggered in multi-mode; may be void
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - float_compare: utility function to compare floats based on specific precision
#  - b64encode, b64decode: functions to encode/decode binary data
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - _logger: _logger.info(message): logger to emit messages in server logs
#  - UserError: exception class for raising user-facing warning messages
#  - Command: x2many commands namespace
# To return an action, assign: action = {...}

for record in records:
    if record.applicant_id:
        applicant = record.applicant_id
        job = applicant.job_id
        applicant_name = applicant.display_name or 'Unknown Applicant'
        job_name = (job.display_name or "No Job") if job else "No Job"
        #record.applicant_id.message_post(body="Processing applicant %s (ID: %s) for job %s" % (applicant_name, applicant.id, job_name))
        
        if job and job.survey_id and job.x_studio_logical_assessment and job.x_studio_emotional_assessment:
            technical_survey = job.survey_id
            logical_survey = job.x_studio_logical_assessment
            emotional_survey = job.x_studio_emotional_assessment

            technical_answer = env['survey.user_input'].search([
                ('survey_id', '=', technical_survey.id),
                ('applicant_id', '=', applicant.id),
                ('state', '=', 'done')
            ], limit=1)

            logical_answer = env['survey.user_input'].search([
                ('survey_id', '=', logical_survey.id),
                ('applicant_id', '=', applicant.id),
                ('state', '=', 'done')
            ], limit=1)

            emotional_answer = env['survey.user_input'].search([
                ('survey_id', '=', emotional_survey.id),
                ('applicant_id', '=', applicant.id),
                ('state', '=', 'done')
            ], limit=1)
            
            if technical_answer and logical_answer and emotional_answer:
                if (technical_answer.scoring_percentage >= 70 and 
                    logical_answer.scoring_percentage >= 70 and 
                    emotional_answer.scoring_percentage >= 70):
                    _logger.info("All survey scores above threshold for applicant %s." % applicant_name)
                    # Only update stage if current stage is 7.
                    if applicant.stage_id.id == 7:
                        _logger.info("Applicant stage is 7, updating to 10 (passed).")
                        applicant.write({'stage_id': 10})
                        applicant.message_post(body="Congratulations! You passed the assessment with scores:\n"
                                                    "Technical: %s%%\nLogical: %s%%\nEmotional: %s%%" % (
                                                        technical_answer.scoring_percentage,
                                                        logical_answer.scoring_percentage,
                                                        emotional_answer.scoring_percentage))
                    else:
                        _logger.info("Applicant stage is not 7, no stage update performed for applicant %s." % applicant_name)
                else:
                    _logger.info("One or more survey scores are below threshold for applicant %s." % applicant_name)
                    applicant.message_post(body="Unfortunately, you did not pass the assessment. Your scores were:\n"
                                                "Technical: %s%%\nLogical: %s%%\nEmotional: %s%%" % (
                                                    technical_answer.scoring_percentage,
                                                    logical_answer.scoring_percentage,
                                                    emotional_answer.scoring_percentage))
                    # Update the applicant's kanban_state to "blocked"
                    applicant.write({'kanban_state': 'blocked'})
            else: 
                applicant.message_post(body="Not all completed, state= %s" % record.state)

