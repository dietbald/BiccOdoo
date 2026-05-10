
action = env['ir.actions.act_window']._for_xml_id('resource.action_resource_calendar_leave_tree')
resource_ids = env['appointment.resource'].search([]).sudo().resource_id
calendar_ids = resource_ids.calendar_id
# we do not care about company-wide as it cannot be set from the leaves wizard
action['domain'] = ['|',
                    '&', ('resource_id', '=', False),
                        '|', ('calendar_id', 'in', calendar_ids.ids), ('calendar_id', '=', False),
                    ('resource_id', 'in', resource_ids.ids)]
    