# This cron is dynamically controlled by Lunch Supplier.
# Do NOT modify this cron, modify the related record instead.
env['lunch.supplier'].browse([1])._send_auto_email()