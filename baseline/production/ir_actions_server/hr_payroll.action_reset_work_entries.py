
# Don't call this server action if you don't want to loose all your work entries
env['hr.work.entry'].search([]).unlink()
now = datetime.datetime.now()
env['hr.version'].write({
    'date_generated_from': now,
    'date_generated_to': now
})
        