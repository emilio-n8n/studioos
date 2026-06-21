VALID_TRANSITIONS = {
    "TODO": ["ASSIGNED", "IN_PROGRESS"],
    "ASSIGNED": ["IN_PROGRESS", "TODO"],
    "IN_PROGRESS": ["REVIEW", "ASSIGNED"],
    "REVIEW": ["APPROVED", "IN_PROGRESS"],
    "APPROVED": ["MERGED", "REVIEW"],
    "MERGED": ["ARCHIVED", "APPROVED"],
    "ARCHIVED": [],
}


def is_valid_transition(current: str, target: str) -> bool:
    return target in VALID_TRANSITIONS.get(current, [])
