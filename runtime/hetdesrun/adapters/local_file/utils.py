from pathlib import Path


def to_url_representation(path: str) -> str:
    """Convert path to a representation that can be used in urls/queries"""
    return path.replace("_", "-_-").replace("/", "__")


def from_url_representation(url_rep: str) -> str:
    """Reconvert url representation of path to actual path"""
    return url_rep.replace("__", "/").replace("-_-", "_")


def is_subpath(base_dir: str | Path, untrusted_path: str | Path) -> bool:
    """Guarantee that untrusted_path is a sub path of (trusted) base_dir

    Should at least complicate path traversal.
    """
    base = Path(base_dir).resolve()
    untrusted = Path(untrusted_path).resolve()
    return untrusted.is_relative_to(base)


def is_trusted_path(
    untrusted_path: str | Path, root_dirs: list[str | Path] | set[str | Path] | set[str]
) -> bool:
    return any(is_subpath(root_dir, untrusted_path) for root_dir in root_dirs)
