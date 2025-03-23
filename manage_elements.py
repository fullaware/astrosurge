"""
manage_elements.py
Manages logic around which elements to mine.
"""
VALID_ELEMENTS = ["gold", "platinum", "iron", "silver"]

def select_elements(user_choice=None):
    if not user_choice:
        return VALID_ELEMENTS
    return [e for e in user_choice if e in VALID_ELEMENTS]
