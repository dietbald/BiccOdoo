
config = model.next() or {}
if config.get('type') not in ('ir.actions.act_window_close',):
    action = config
