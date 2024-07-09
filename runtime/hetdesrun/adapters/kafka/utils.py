def to_url_representation(path: str) -> str:
    """Convert path to a representation that can be used in urls/queries"""
    return path.replace("_", "-_-").replace("/", "__")


def from_url_representation(url_rep: str) -> str:
    """Reconvert url representation of path to actual path"""
    return url_rep.replace("__", "/").replace("-_-", "_")


def parse_value_and_msg_identifier(
    combined_value_key_msg_identifier: str,
) -> tuple[str, str]:
    """Split str at ":" into message identifier and value key

    Default to empty message identifier if no ":" is found.
    """
    parts = combined_value_key_msg_identifier.split(":", maxsplit=1)

    if len(parts) == 1:
        return "", parts[0]  # empty message identifier

    # 2 parts
    msg_identifier, value_key = parts
    return msg_identifier, value_key
