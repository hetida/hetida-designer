def to_url_representation(path: str) -> str:
    """Convert path to a representation that can be used in urls/queries"""
    return path.replace("_", "._.").replace("/", "__")


def from_url_representation(url_rep: str) -> str:
    """Reconvert url representation of path to actual path"""
    return url_rep.replace("__", "/").replace("._.", "_")
