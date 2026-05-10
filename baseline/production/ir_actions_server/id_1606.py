text_date = record.x_studio_closing_date
result_date = False

if text_date:
    text_date = text_date.strip()

    # Remove any time part (e.g. "2025-10-28 14:30:00" → "2025-10-28")
    for sep in [" ", "T"]:
        if sep in text_date:
            text_date = text_date.split(sep)[0]
            break

    def manual_parse(date_str):
        # Split by possible separators
        if "-" in date_str:
            parts = date_str.split("-")
        elif "/" in date_str:
            parts = date_str.split("/")
        else:
            return False

        # Cleanup: remove empty parts or stray chars
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) != 3:
            return False

        # Try to detect the pattern
        try:
            if len(parts[0]) == 4:  # yyyy-mm-dd or yyyy/mm/dd
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            elif len(parts[2]) == 4:  # dd/mm/yyyy or mm/dd/yyyy
                d1, d2, y = int(parts[0]), int(parts[1]), int(parts[2])
                if d1 > 12:  # if first number > 12, assume dd/mm/yyyy
                    d, m = d1, d2
                else:  # else assume mm/dd/yyyy
                    d, m = d2, d1
            else:
                return False
        except Exception:
            return False

        # Validate that the date is real (no datetime import!)
        if not (1 <= m <= 12):
            return False
        days_in_month = {
            1: 31, 2: 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28,
            3: 31, 4: 30, 5: 31, 6: 30,
            7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
        }
        if not (1 <= d <= days_in_month[m]):
            return False

        # Return normalized Odoo format (YYYY-MM-DD)
        return f"{y:04d}-{m:02d}-{d:02d}"

    try:
        result_date = manual_parse(text_date)
    except Exception:
        result_date = False

# Safe ORM write (no forbidden STORE_ATTR)
record.update({'x_studio_final_closing_date': result_date or False})
