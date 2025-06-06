from datetime import date, datetime


def parse_date(val):
    if isinstance(val, date):
        return val

    if not val:
        return None

    formats = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%d.%m.%Y"]

    for fmt in formats:
        try:
            return datetime.strptime(val.strip(), fmt).date()
        except (ValueError, TypeError):
            continue

    print(f"[parse_date] Failed to parse date: {val}")
    return None