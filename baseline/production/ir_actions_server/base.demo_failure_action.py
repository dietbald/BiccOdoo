
failures = env['ir.demo_failure'].search([
    ('wizard_id', '=', False),
])
record = model.create({
    'failure_ids': [Command.set(failures.ids)],
})
action = {
    'type': 'ir.actions.act_window',
    'res_id': record.id,
    'res_model': 'ir.demo_failure.wizard',
    'target': 'new',
    'views': [(env.ref('base.demo_failures_dialog').id, 'form')],
}
        