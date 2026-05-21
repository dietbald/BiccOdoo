# TRIGGER: Manual — Action menu on hr.applicant (form + list)
# MODEL: hr.applicant
# DESCRIPTION: Archive every TEST_FIXTURE_* applicant and delete the
#   survey.user_input rows we seeded (matched by the bicc-fixture-*
#   email pattern). Safe to run anywhere — keyed by name prefix, so
#   it can't touch real applicants.
#
# Pure procedural — no closures.

fixtures = env['hr.applicant'].with_context(active_test=False).search([
    ('name', '=ilike', 'TEST_FIXTURE_%'),
])
fixture_count = len(fixtures)
if fixtures:
    fixtures.write({'active': False})

inputs = env['survey.user_input'].search([
    ('email', '=ilike', 'bicc-fixture-%@mailinator.com'),
])
input_count = len(inputs)
if inputs:
    inputs.unlink()

action = {
    'type': 'ir.actions.client',
    'tag': 'display_notification',
    'params': {
        'title': 'BICC TEST: Fixtures reset',
        'message': 'Archived %d applicant(s) and deleted %d survey input(s).' % (fixture_count, input_count),
        'type': 'success',
        'sticky': False,
    },
}
