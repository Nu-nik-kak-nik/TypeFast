def safe_float_convert(value: str | int | float | None, default: float = 0.0) -> float:
    try:
        if isinstance(value, str):
            value = value.rstrip("%")
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_str_convert(value: str | int | float | None, default: str = "") -> str:
    return str(value) if value is not None else default
