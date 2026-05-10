now = datetime.datetime.now()
for rec in records:
    rec.message_post(body=f"N8N webhook automation triggered at {now}")