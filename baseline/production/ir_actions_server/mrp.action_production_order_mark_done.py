
            if records:
                res = records.filtered(lambda mo: mo.state in {'confirmed', 'to_close', 'progress'}).button_mark_done()
                if res is not True:
                    action = res
            