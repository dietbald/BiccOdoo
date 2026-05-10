
employees = env['hr.employee'].browse(env.context.get('selected_ids', []))
if employees:
    action = employees.action_create_users()
            