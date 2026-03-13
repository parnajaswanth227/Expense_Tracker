"""
resources/category_resource.py
───────────────────────────────
MCP resource that exposes the full category taxonomy from categories.json.
"""

import json
import os

_PROJECT_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CATEGORIES_PATH = os.path.join(_PROJECT_ROOT, "categories.json")


def load_categories() -> dict:
    """
    Load and return the full category → subcategory mapping.

    Returns:
        dict  e.g. {"food": ["groceries", "dining_out", ...], ...}
    """
    with open(_CATEGORIES_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)
