import re

def has_invalid_chars(text: str) -> bool:
    """Used for better ProjectNaming"""
    return bool(re.search(r"[^a-zA-Z0-9 _]", text))

def get_by_id(items, target_id):
    """Speed run getting the targeted object!"""
    for item in items:
        if item.get("id") == target_id:
            return item
    return None