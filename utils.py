"""utils.py — shared helpers."""

from datetime import datetime


def validate_date(date_str: str) -> dict | None:
    if not date_str or not isinstance(date_str, str):
        return {"error": "Date is required in YYYY-MM-DD format."}
    try:
        datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        return {"error": f"Invalid date format. Expected YYYY-MM-DD, got: '{date_str}'"}
    return None
