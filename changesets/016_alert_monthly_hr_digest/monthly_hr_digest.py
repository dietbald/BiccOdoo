# TRIGGER: Weekly Scheduled Action (every Monday 8:00 AM PHT) —
#   but only sends on the LAST Monday of each month (script-side gate).
# MODEL: hr.employee
# DESCRIPTION: Monthly HR digest per company. Sections:
#   1. Birthdays next month
#   2. Work anniversary milestones (6mo, 1y, 2y, 3y, 5y, 10y, 15y, 20y, 25y)
#   3. Contracts expiring next month (red highlight for first 2 weeks)
#   4. Public holidays next month
#   5. Headcount summary by department

now = datetime.datetime.now()

# Last-Monday-of-month gate: if next Monday is still in the same month,
# this is NOT the last Monday yet → exit silently.
next_monday = now + datetime.timedelta(days=7)
if next_monday.month == now.month:
    log("Monthly HR digest: not last Monday of month — skipping.")
else:
    # Next month's date range
    if now.month == 12:
        next_month = 1
        next_year = now.year + 1
    else:
        next_month = now.month + 1
        next_year = now.year

    if next_month == 12:
        last_day = 31
    else:
        last_day = (datetime.date(next_year, next_month + 1, 1) - datetime.timedelta(days=1)).day

    month_name = datetime.date(next_year, next_month, 1).strftime('%B %Y')
    first_of_next = datetime.date(next_year, next_month, 1)
    last_of_next = datetime.date(next_year, next_month, last_day)
    midpoint = datetime.date(next_year, next_month, 14)

    hr_group = env.ref('hr.group_hr_manager', raise_if_not_found=False)
    notify_partners = env['res.partner']
    if hr_group:
        notify_partners = hr_group.user_ids.filtered('active').mapped('partner_id')

    if not notify_partners:
        log("Monthly HR digest: no HR Manager group members — skipping.")
    else:
        table_style = "border-collapse:collapse;width:100%;margin-bottom:20px;"
        th_style = "background-color:#2c3e50;color:white;padding:8px 12px;text-align:left;font-size:13px;"
        td_style = "padding:8px 12px;border-bottom:1px solid #e0e0e0;font-size:13px;"
        td_red_style = "padding:8px 12px;border-bottom:1px solid #e0e0e0;font-size:13px;color:#c0392b;font-weight:bold;"

        # Pre-build recipient command list (no comp capturing outer var)
        recipient_cmds = []
        for pid in notify_partners.ids:
            recipient_cmds.append((4, pid))

        all_companies = env['res.company'].sudo().search([])
        for company in all_companies:
            company_name = company.name or 'Our Company'
            employees = env['hr.employee'].sudo().search([('company_id', '=', company.id)])
            if not employees:
                continue

            # 1. BIRTHDAYS
            birthday_emps_sortable = []
            for emp in employees:
                if emp.birthday and emp.birthday.month == next_month:
                    birthday_emps_sortable.append((emp.birthday.day, emp.id, emp))
            birthday_emps_sortable.sort()

            birthday_rows = ""
            for _day, _id, emp in birthday_emps_sortable:
                bday_str = emp.birthday.strftime('%B %d')
                dept = emp.department_id.name if emp.department_id else '-'
                job = emp.job_id.name if emp.job_id else '-'
                birthday_rows += (
                    "<tr><td style='%s'>%s</td><td style='%s'>%s</td>"
                    "<td style='%s'>%s</td><td style='%s'>%s</td></tr>"
                ) % (td_style, emp.name, td_style, bday_str, td_style, dept, td_style, job)

            # 2. WORK ANNIVERSARY MILESTONES
            milestones_years = {1: '1 Year', 2: '2 Years', 3: '3 Years', 5: '5 Years',
                                10: '10 Years', 15: '15 Years', 20: '20 Years', 25: '25 Years'}

            anniversary_emps_sortable = []
            for emp in employees:
                if not emp.date_start:
                    continue
                if emp.date_start.month != next_month:
                    continue
                years_diff = next_year - emp.date_start.year
                months_diff = (next_year - emp.date_start.year) * 12 + (next_month - emp.date_start.month)
                milestone = None
                if months_diff == 6:
                    milestone = '6 Months'
                elif months_diff % 12 == 0 and years_diff in milestones_years:
                    milestone = milestones_years[years_diff]
                if milestone:
                    # Sort descending by months_diff → key is -months_diff
                    anniversary_emps_sortable.append((-months_diff, emp.id, emp, milestone))
            anniversary_emps_sortable.sort()

            anniversary_rows = ""
            for _neg_months, _id, emp, milestone in anniversary_emps_sortable:
                dept = emp.department_id.name if emp.department_id else '-'
                start_str = emp.date_start.strftime('%B %d, %Y')
                anniversary_rows += (
                    "<tr><td style='%s'>%s</td><td style='%s'>%s</td>"
                    "<td style='%s'>%s</td><td style='%s'>%s</td></tr>"
                ) % (td_style, emp.name, td_style, start_str, td_style, milestone, td_style, dept)

            # 3. EXPIRING CONTRACTS
            expiring = env['hr.employee'].sudo().search([
                ('company_id', '=', company.id),
                ('contract_date_end', '>=', str(first_of_next)),
                ('contract_date_end', '<=', str(last_of_next)),
            ])

            contract_rows = ""
            early_count = 0
            for emp in expiring:
                dept = emp.department_id.name if emp.department_id else '-'
                job = emp.job_id.name if emp.job_id else '-'
                end_str = emp.contract_date_end.strftime('%B %d, %Y')
                is_early = emp.contract_date_end <= midpoint
                style = td_red_style if is_early else td_style
                if is_early:
                    early_count += 1
                contract_rows += (
                    "<tr><td style='%s'>%s</td><td style='%s'>%s</td>"
                    "<td style='%s'>%s</td><td style='%s'>%s</td></tr>"
                ) % (style, emp.name, style, end_str, style, job, style, dept)

            # 4. PUBLIC HOLIDAYS
            holidays = env['resource.calendar.leaves'].sudo().search([
                ('resource_id', '=', False),
                ('company_id', '=', company.id),
                ('date_from', '>=', str(first_of_next)),
                ('date_from', '<=', str(last_of_next) + ' 23:59:59'),
            ], order='date_from')

            holiday_rows = ""
            for h in holidays:
                h_date = h.date_from.strftime('%B %d, %Y (%A)')
                holiday_rows += "<tr><td style='%s'>%s</td><td style='%s'>%s</td></tr>" % (
                    td_style, h.name or '-', td_style, h_date)

            # 5. HEADCOUNT BY DEPARTMENT
            total_count = len(employees)
            dept_counts = {}
            for emp in employees:
                dept = emp.department_id.name if emp.department_id else 'Unassigned'
                dept_counts[dept] = dept_counts.get(dept, 0) + 1

            # Sort dept_counts by count desc using plain tuple sort (no lambda)
            dept_sortable = []
            for dept, count in dept_counts.items():
                dept_sortable.append((-count, dept))
            dept_sortable.sort()

            headcount_rows = ""
            for _neg_count, dept in dept_sortable:
                count = dept_counts[dept]
                headcount_rows += "<tr><td style='%s'>%s</td><td style='%s'>%d</td></tr>" % (
                    td_style, dept, td_style, count)

            # Build email
            body_html = "<div style='font-family:Roboto,Arial,sans-serif;color:#101820;font-size:13px;line-height:1.6;'>"
            body_html += "<h2 style='color:#2c3e50;'>%s - Monthly HR Digest for %s</h2>" % (company_name, month_name)

            body_html += "<h3 style='color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:5px;'>Birthdays Next Month</h3>"
            if birthday_rows:
                body_html += "<table style='%s'><thead><tr><th style='%s'>Name</th><th style='%s'>Birthday</th><th style='%s'>Department</th><th style='%s'>Job Title</th></tr></thead><tbody>%s</tbody></table>" % (
                    table_style, th_style, th_style, th_style, th_style, birthday_rows)
                body_html += "<p><b>%d</b> birthday(s) next month.</p>" % len(birthday_emps_sortable)
            else:
                body_html += "<p>No birthdays next month.</p>"

            body_html += "<h3 style='color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:5px;'>Work Anniversary Milestones</h3>"
            if anniversary_rows:
                body_html += "<table style='%s'><thead><tr><th style='%s'>Name</th><th style='%s'>Start Date</th><th style='%s'>Milestone</th><th style='%s'>Department</th></tr></thead><tbody>%s</tbody></table>" % (
                    table_style, th_style, th_style, th_style, th_style, anniversary_rows)
            else:
                body_html += "<p>No milestone anniversaries next month.</p>"

            body_html += "<h3 style='color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:5px;'>Contracts Expiring Next Month</h3>"
            if contract_rows:
                body_html += "<table style='%s'><thead><tr><th style='%s'>Name</th><th style='%s'>Contract End</th><th style='%s'>Job Title</th><th style='%s'>Department</th></tr></thead><tbody>%s</tbody></table>" % (
                    table_style, th_style, th_style, th_style, th_style, contract_rows)
                if early_count:
                    body_html += "<p style='color:#c0392b;'><b>%d</b> contract(s) expiring in the first 2 weeks - action needed soon.</p>" % early_count
            else:
                body_html += "<p>No contracts expiring next month.</p>"

            body_html += "<h3 style='color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:5px;'>Public Holidays Next Month</h3>"
            if holiday_rows:
                body_html += "<table style='%s'><thead><tr><th style='%s'>Holiday</th><th style='%s'>Date</th></tr></thead><tbody>%s</tbody></table>" % (
                    table_style, th_style, th_style, holiday_rows)
            else:
                body_html += "<p><i>No public holidays configured for next month.</i></p>"

            body_html += "<h3 style='color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:5px;'>Headcount Summary</h3>"
            body_html += "<p><b>Total active employees: %d</b></p>" % total_count
            body_html += "<table style='%s'><thead><tr><th style='%s'>Department</th><th style='%s'>Count</th></tr></thead><tbody>%s</tbody></table>" % (
                table_style, th_style, th_style, headcount_rows)

            body_html += "<hr style='border:none;border-top:1px solid #e0e0e0;margin:20px 0;'/>"
            body_html += "<p style='color:#7f8c8d;font-size:11px;'>Automated monthly digest. Generated %s.</p>" % now.strftime('%B %d, %Y at %I:%M %p')
            body_html += "</div>"

            env['mail.mail'].sudo().create({
                'subject': '%s Monthly HR Digest - %s' % (company_name, month_name),
                'body_html': body_html,
                'recipient_ids': recipient_cmds,
                'auto_delete': True,
            }).send()
            log("Monthly HR digest sent for company '%s' (%s)" % (company_name, month_name))
