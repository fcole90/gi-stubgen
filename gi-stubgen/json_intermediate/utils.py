def infer_type(value: str) -> str:
    _value = value
    # Make remove minus sign from negative numbers
    if _value.startswith("-"):
        _value = _value[1:]

    if "." in _value:
        split_value = _value.split(".")
        if len(split_value) == 2 and split_value[0].isdigit() and split_value[1].isdigit():
            return "float"

    if _value.isdigit():
        return "int"

    return "str"


def to_inferred_type(value: str) -> str | float | int:
    value_type = infer_type(value)

    try:
        if value_type == "int":
            return int(value)

        if value_type == "float":
            return float(value)
    except Exception:
        print(
            f"Warning: Expected {value} to be '{value_type}' but conversion failed")
        return value
    return value
