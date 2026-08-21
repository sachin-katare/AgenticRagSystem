from collections.abc import Mapping


SENSITIVE_KEYS = {"answer", "text", "content", "prompt", "password", "token", "secret"}


def safe_log_fields(fields: Mapping[str, object]) -> dict[str, object]:
    """Return log fields with risky large-text or secret-like values removed."""
    safe_fields: dict[str, object] = {}
    for key, value in fields.items():
        if key.lower() in SENSITIVE_KEYS:
            safe_fields[key] = "[redacted]"
        else:
            safe_fields[key] = value
    return safe_fields
