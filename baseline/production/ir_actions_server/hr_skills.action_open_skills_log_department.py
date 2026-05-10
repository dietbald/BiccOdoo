
action = env['ir.actions.act_window']._for_xml_id('hr_skills.action_hr_employee_skill_log_department')
action['domain'] = [('department_id', '=', record.id)]
        