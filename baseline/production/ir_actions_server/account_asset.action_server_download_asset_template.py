
active_company = env.company
url = f'/web/binary/download_asset_template/{active_company.id}'
action = {
    'type': 'ir.actions.act_url',
    'url': url,
    'target': 'download',
}
    