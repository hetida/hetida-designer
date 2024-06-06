import random
from uuid import UUID


def get_uuid_from_seed(seed_str: str) -> UUID:
    """Generate UUID from string

    The seed_str is used to reset the random number generation seed so that this
    function always returns same UUID for the same seed_str.

    This may be used to get reproducible UUIDs from human-readable strings in scripts
    and tests. Should not be used anywhere else for security reasons.
    """
    random.seed(seed_str)
    return UUID(int=random.getrandbits(128))


def get_id_str_from_seed(seed_str: str) -> str:
    """Generate UUID string from string

    The seed_str is used to reset the random number generation seed so that this
    function always returns same UUID string for the same seed_str.

    This may be used to get reproducible UUID strings from human-readable strings in scripts
    and tests. Should not be used anywhere else for security reasons.
    """
    return str(get_uuid_from_seed(seed_str))
