now = datetime.datetime.now()

for rec in records:
    msgs = env["mail.message"].search([
        ("model", "=", rec._name),
        ("res_id", "=", rec.id),
        ("date", "=", False),
    ])
    # bulk write updates all matched rows, not just the first
    msgs.write({"date": now})