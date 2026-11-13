import re


def is_valid_email(email: str) -> bool:
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None


def is_valid_name(name: str) -> bool:
    allowed_punctuation = " -'.’"
    return (
        any(character.isalpha() for character in name)
        and all(character.isalpha() or character in allowed_punctuation for character in name)
    )
